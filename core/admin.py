from django.contrib import admin
from django import forms
from .models import ChatSession, Message, Note, APIKey
from .services.encryption import encrypt_key, decrypt_key, mask_key


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at", "updated_at")
    list_filter = ("user",)
    search_fields = ("title",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "short_content", "created_at", "is_discarded")
    list_filter = ("role", "is_discarded")
    search_fields = ("content",)

    def short_content(self, obj):
        return obj.content[:60] + ("..." if len(obj.content) > 60 else "")
    short_content.short_description = "Content"


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at")
    list_filter = ("user",)
    search_fields = ("title", "content", "tags")


class APIKeyAdminForm(forms.ModelForm):
    """
    Custom form that accepts a plain API key and encrypts it on save.
    The plain key field is only shown when adding a new key, not when editing.
    """
    plain_key = forms.CharField(
        label="Gemini API Key (plain)",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "vTextField",
            "placeholder": "AIzaSy...",
            "style": "width: 500px; font-family: monospace;",
        }),
        help_text="Paste the raw Gemini API key. It will be encrypted before saving.",
    )

    class Meta:
        model = APIKey
        fields = ("name", "is_active")

    def save(self, commit=True):
        instance = super().save(commit=False)
        plain = self.cleaned_data.get("plain_key")
        if plain:
            instance.encrypted_key = encrypt_key(plain.strip())
        if commit:
            instance.save()
        return instance


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    form = APIKeyAdminForm

    list_display = (
        "id", "name", "is_active",
        "masked_preview", "requests_today",
        "last_used_at", "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = (
        "requests_this_minute", "requests_today",
        "minute_window_start", "day_window_start",
        "last_used_at", "last_error",
        "created_at", "updated_at",
    )

    fieldsets = (
        ("Key details", {
            "fields": ("name", "is_active", "plain_key"),
            "description": "Paste the raw API key. Leave 'plain_key' empty to keep the existing key.",
        }),
        ("Usage stats (read-only)", {
            "fields": (
                "requests_this_minute", "requests_today",
                "minute_window_start", "day_window_start",
                "last_used_at", "last_error",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def masked_preview(self, obj):
        if not obj.encrypted_key:
            return "—"
        try:
            plain = decrypt_key(obj.encrypted_key)
            return mask_key(plain)
        except Exception:
            return "⚠️ unreadable"
    masked_preview.short_description = "Key"

    def get_form(self, request, obj=None, **kwargs):
        """
        When editing an existing key, hide the 'plain_key' field's required check.
        When adding a new key, require it.
        """
        form = super().get_form(request, obj, **kwargs)

        if obj is None:
            # Adding a new key
            form.base_fields["plain_key"].required = True
        else:
            form.base_fields["plain_key"].required = False

        return form