from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import User


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create an authentication token for newly created users."""
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=User)
def claim_pending_judge_invites(sender, instance=None, created=False, **kwargs):
    """Convert any pending judge invites for this email into real assignments."""
    if not created:
        return

    from apps.competitions.models import PendingJudgeInvite, JudgeAssignment
    from apps.notifications.models import Notification

    pending = PendingJudgeInvite.objects.filter(email=instance.email).select_related('competition', 'invited_by')
    for invite in pending:
        JudgeAssignment.objects.get_or_create(
            competition=invite.competition,
            judge=instance,
            defaults={'status': 'invited'}
        )
        inviter_name = invite.invited_by.get_full_name() or invite.invited_by.email
        Notification.objects.create(
            user=instance,
            title='Judge Invitation',
            message=f'{inviter_name} invited you to judge "{invite.competition.title}".',
            notification_type='judge_invited',
            related_object_id=str(invite.competition.id),
            related_object_type='competition'
        )
    pending.delete()
