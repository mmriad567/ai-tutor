import os
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from core.models import APIKey
from core.services.encryption import decrypt_key


# Per-key rate limits (Gemini free tier defaults).
# Configurable via .env — see GEMINI_RPM_PER_KEY and GEMINI_RPD_PER_KEY.
RPM_LIMIT = int(os.getenv("GEMINI_RPM_PER_KEY", "15"))
RPD_LIMIT = int(os.getenv("GEMINI_RPD_PER_KEY", "1500"))

# Fixed window size for the minute counter.
MINUTE_WINDOW = timedelta(seconds=60)


class NoKeyAvailableError(Exception):
    """Raised when no API key can serve the request right now."""
    pass


class KeyExhaustedError(Exception):
    """Raised when the chosen key returns a hard limit error (e.g. 429)."""
    pass


def _refresh_counters(api_key: APIKey) -> bool:
    """
    Reset per-minute and per-day counters if their windows have expired.
    Returns True if the object was modified in-memory (but not yet saved).
    """
    now = timezone.now()
    today = now.date()
    modified = False

    # --- Minute window ---
    if api_key.minute_window_start is None:
        api_key.minute_window_start = now
        api_key.requests_this_minute = 0
        modified = True
    elif (now - api_key.minute_window_start) >= MINUTE_WINDOW:
        api_key.requests_this_minute = 0
        api_key.minute_window_start = now
        modified = True

    # --- Day window ---
    if api_key.day_window_start is None:
        api_key.day_window_start = today
        api_key.requests_today = 0
        modified = True
    elif api_key.day_window_start != today:
        api_key.requests_today = 0
        api_key.day_window_start = today
        modified = True

    return modified


def _is_available(api_key: APIKey) -> bool:
    """True if the key still has capacity in both windows."""
    return (
        api_key.requests_this_minute < RPM_LIMIT
        and api_key.requests_today < RPD_LIMIT
    )


def acquire_key() -> APIKey:
    """
    Pick the least-used available API key, mark it as used, and return it.
    This function is atomic — two simultaneous calls will not clash.

    Raises:
        NoKeyAvailableError: if every active key has hit a limit.
    """
    with transaction.atomic():
        # Fetch all active keys, lock nothing (SQLite locks the whole DB anyway).
        keys = list(APIKey.objects.filter(is_active=True).order_by("id"))

        if not keys:
            raise NoKeyAvailableError(
                "কোনো API key কনফিগার করা হয়নি। Admin panel থেকে key যোগ করো।"
            )

        # Refresh all windows first
        touched = []
        for key in keys:
            if _refresh_counters(key):
                touched.append(key)

        # Save the ones whose counters we reset
        for key in touched:
            key.save(update_fields=[
                "requests_this_minute",
                "requests_today",
                "minute_window_start",
                "day_window_start",
            ])

        # Filter to keys with remaining capacity
        available = [k for k in keys if _is_available(k)]

        if not available:
            raise NoKeyAvailableError(
                "এই মিনিটে সব API key-এর লিমিট শেষ। একটু পরে আবার চেষ্টা করো।"
            )

        # Least-used-first strategy
        chosen = min(available, key=lambda k: (k.requests_this_minute, k.requests_today))

        # Reserve the slot
        chosen.requests_this_minute += 1
        chosen.requests_today += 1
        chosen.last_used_at = timezone.now()
        chosen.save(update_fields=[
            "requests_this_minute",
            "requests_today",
            "last_used_at",
        ])

        return chosen


def get_plain_key(api_key: APIKey) -> str:
    """Decrypt and return the raw Gemini key for use in an API call."""
    return decrypt_key(api_key.encrypted_key)


def record_failure(api_key: APIKey, error_message: str) -> None:
    """Save the last error on a key for diagnostics."""
    api_key.last_error = (error_message or "")[:1000]
    api_key.save(update_fields=["last_error"])


def record_success(api_key: APIKey) -> None:
    """Clear the last error after a successful call."""
    if api_key.last_error:
        api_key.last_error = ""
        api_key.save(update_fields=["last_error"])


def get_stats() -> dict:
    """Return a summary of all keys for the admin dashboard."""
    keys = APIKey.objects.all().order_by("id")
    return {
        "total_keys": keys.count(),
        "active_keys": keys.filter(is_active=True).count(),
        "total_requests_today": sum(k.requests_today for k in keys),
        "total_requests_this_minute": sum(k.requests_this_minute for k in keys),
        "per_key": [
            {
                "name": k.name,
                "active": k.is_active,
                "requests_this_minute": k.requests_this_minute,
                "requests_today": k.requests_today,
                "last_used_at": k.last_used_at,
                "last_error": k.last_error,
            }
            for k in keys
        ],
    }
