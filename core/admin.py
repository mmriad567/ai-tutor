from django.contrib import admin
from .models import ChatSession, Message, Note, APIKey


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


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "requests_today", "last_used_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("requests_this_minute", "requests_today", "last_used_at", "last_error")
    fieldsets = (
        (None, {
            'fields': ('name', 'encrypted_key', 'is_active')
        }),
    )