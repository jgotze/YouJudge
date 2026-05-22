from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Notification


@shared_task
def send_notification_email(notification_id):
    """Send notification via email."""
    try:
        notification = Notification.objects.get(id=notification_id)

        # Check if user has email notifications enabled
        if not notification.user.email_notifications:
            return "User has email notifications disabled"

        # Check if already sent
        if notification.is_sent_via_email:
            return "Email already sent"

        subject = f'YouJudge: {notification.title}'
        message = render_to_string('notifications/email/notification.html', {
            'notification': notification,
            'user': notification.user,
        })

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [notification.user.email],
            fail_silently=False,
            html_message=message,
        )

        notification.is_sent_via_email = True
        notification.save()

        return f"Email sent to {notification.user.email}"
    except Notification.DoesNotExist:
        return "Notification not found"
