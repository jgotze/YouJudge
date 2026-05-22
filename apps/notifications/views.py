from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Notification


@login_required
def notifications_list_view(request):
    """Display all notifications for the user."""
    from apps.competitions.models import JudgeAssignment

    filter_type = request.GET.get('filter', 'all')

    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    if filter_type == 'invites':
        qs = qs.filter(notification_type__in=Notification.INVITE_TYPES)

    notifications = list(qs)
    for notification in notifications:
        notification.pending_assignment = None
        if notification.notification_type in Notification.INVITE_TYPES and notification.related_object_id:
            try:
                notification.pending_assignment = JudgeAssignment.objects.get(
                    competition__id=notification.related_object_id,
                    judge=request.user,
                    status='invited'
                )
            except JudgeAssignment.DoesNotExist:
                pass

    pending_invite_count = Notification.objects.filter(
        user=request.user,
        notification_type__in=Notification.INVITE_TYPES
    ).count()

    context = {
        'notifications': notifications,
        'filter_type': filter_type,
        'pending_invite_count': pending_invite_count,
    }
    return render(request, 'notifications/notifications_list.html', context)


@login_required
def notification_mark_read_view(request, pk):
    """Mark a notification as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()

    # Redirect to related object if available
    url = notification.get_url()
    if url and url != '#':
        return redirect(url)

    return redirect('notifications:list')


@login_required
def notifications_mark_all_read_view(request):
    """Mark all notifications as read."""
    Notification.mark_all_as_read(request.user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('notifications:list')


@login_required
def notifications_unread_count_view(request):
    """Get unread notifications count (AJAX endpoint)."""
    count = Notification.get_unread_count(request.user)
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]

    return JsonResponse({
        'count': count,
        'notifications': [{
            'id': str(n.id),
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.isoformat(),
            'url': n.get_url(),
        } for n in notifications]
    })
