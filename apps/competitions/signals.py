from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JudgeAssignment, Entry
from apps.notifications.models import Notification


@receiver(post_save, sender=JudgeAssignment)
def notify_judge_assignment(sender, instance, created, **kwargs):
    """Notify judge when assigned to a competition."""
    if created:
        Notification.objects.create(
            user=instance.judge,
            title='Judge Assignment',
            message=f'You have been invited to judge "{instance.competition.title}"',
            notification_type='judge_invite',
            related_object_id=str(instance.competition.id),
            related_object_type='competition'
        )


@receiver(post_save, sender=Entry)
def notify_new_entry(sender, instance, created, **kwargs):
    """Notify competition creator when new entry is submitted."""
    if created:
        Notification.objects.create(
            user=instance.competition.created_by,
            title='New Entry Submitted',
            message=f'New entry "{instance.title}" submitted to "{instance.competition.title}"',
            notification_type='new_entry',
            related_object_id=str(instance.competition.id),
            related_object_type='competition'
        )
