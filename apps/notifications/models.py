from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel
import uuid


class Notification(SoftDeleteModel):
    NOTIFICATION_TYPES = [
        ('judge_invite', 'Judge Invitation'),
        ('judge_invited', 'Judge Invitation'),
        ('judge_accepted', 'Judge Accepted'),
        ('new_entry', 'New Entry'),
        ('competition_started', 'Competition Started'),
        ('competition_ended', 'Competition Ended'),
        ('scoring_complete', 'Scoring Complete'),
        ('general', 'General'),
    ]

    INVITE_TYPES = ('judge_invite', 'judge_invited')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('user')
    )
    title = models.CharField(_('title'), max_length=255)
    message = models.TextField(_('message'))
    notification_type = models.CharField(
        _('notification type'),
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='general'
    )

    related_object_id = models.CharField(_('related object ID'), max_length=255, blank=True)
    related_object_type = models.CharField(_('related object type'), max_length=50, blank=True)

    is_read = models.BooleanField(_('is read'), default=False)
    is_sent_via_email = models.BooleanField(_('sent via email'), default=False)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    read_at = models.DateTimeField(_('read at'), blank=True, null=True)

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.user.email}: {self.title}'

    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def get_url(self):
        from django.urls import reverse
        if self.related_object_type == 'competition' and self.related_object_id:
            return reverse('competitions:detail', kwargs={'pk': self.related_object_id})
        return '#'

    @classmethod
    def mark_all_as_read(cls, user):
        from django.utils import timezone
        cls.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )

    @classmethod
    def get_unread_count(cls, user):
        return cls.objects.filter(user=user, is_read=False).count()
