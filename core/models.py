from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    title = models.CharField(max_length=200, default="নতুন ক্লাস")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} — {self.title}"


class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "user"),
        ("assistant", "assistant"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    prompt_text = models.TextField(blank=True, default="")
    audio_file = models.FileField(upload_to="audio/", blank=True, null=True)
    image_file = models.FileField(upload_to="images/", blank=True, null=True)
    is_discarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = self.content[:40] if self.content else "(empty)"
        return f"[{self.role}] {preview}"


class Note(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    source_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    tags = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class APIKey(models.Model):
    """
    Gemini API keys managed by the admin.
    All users share these keys via a rotation system.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identifying name like 'Key 1', 'Key 2'"
    )
    encrypted_key = models.TextField(
        help_text="Fernet-encrypted Gemini API key"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Disable to skip this key during rotation"
    )

    # Usage tracking for rotation
    requests_this_minute = models.IntegerField(default=0)
    requests_today = models.IntegerField(default=0)
    minute_window_start = models.DateTimeField(auto_now_add=True)
    day_window_start = models.DateField(auto_now_add=True)

    last_used_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({status})"