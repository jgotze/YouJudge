from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_verification_email(user_id, token):
    """Send email verification link to user."""
    try:
        user = User.objects.get(id=user_id)
        verification_link = f"{settings.SITE_URL}/accounts/verify/{token}/"

        subject = 'Verify your YouJudge account'
        message = render_to_string('accounts/emails/verification_email.html', {
            'user': user,
            'verification_link': verification_link,
        })

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        return f"Verification email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"


@shared_task
def send_judge_invite_email(judge_id, competition_title, inviter_name, dashboard_url):
    """Send email to an existing user invited to judge a competition."""
    try:
        user = User.objects.get(id=judge_id)
        subject = f'You\'ve been invited to judge "{competition_title}"'
        message = render_to_string('accounts/emails/judge_invite_email.html', {
            'user': user,
            'competition_title': competition_title,
            'inviter_name': inviter_name,
            'dashboard_url': dashboard_url,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email],
                  fail_silently=False, html_message=message)
        return f"Judge invite sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"


@shared_task
def send_external_judge_invite_email(email, competition_title, inviter_name, register_url):
    """Send email to someone without an account, inviting them to join and judge."""
    subject = f'You\'ve been invited to judge "{competition_title}" on YouJudge'
    message = render_to_string('accounts/emails/external_judge_invite_email.html', {
        'email': email,
        'competition_title': competition_title,
        'inviter_name': inviter_name,
        'register_url': register_url,
    })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email],
              fail_silently=False, html_message=message)
    return f"External judge invite sent to {email}"


@shared_task
def send_password_reset_email(user_id, token):
    """Send password reset link to user."""
    try:
        user = User.objects.get(id=user_id)
        reset_link = f"{settings.SITE_URL}/accounts/password-reset/{token}/"

        subject = 'Reset your YouJudge password'
        message = render_to_string('accounts/emails/password_reset_email.html', {
            'user': user,
            'reset_link': reset_link,
        })

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        return f"Password reset email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"
