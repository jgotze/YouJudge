from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = ['user', 'title', 'notification_type', 'is_read', 'is_sent_via_email', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_sent_via_email', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']

    fieldsets = (
        ('Notification', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent_via_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at')
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
