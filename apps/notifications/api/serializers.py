from rest_framework import serializers
from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type',
            'related_object_id', 'related_object_type', 'is_read',
            'is_sent_via_email', 'created_at', 'read_at', 'url'
        ]
        read_only_fields = [
            'id', 'user', 'is_sent_via_email', 'created_at', 'read_at', 'url'
        ]

    def get_url(self, obj):
        """Get URL related to notification."""
        return obj.get_url()
