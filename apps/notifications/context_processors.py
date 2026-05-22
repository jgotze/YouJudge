from .models import Notification


def notifications_processor(request):
    """Add notification count to all templates."""
    if request.user.is_authenticated:
        unread_count = Notification.get_unread_count(request.user)
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        unread_invite_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            notification_type__in=Notification.INVITE_TYPES
        ).count()

        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
            'unread_invite_count': unread_invite_count,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'unread_invite_count': 0,
    }
