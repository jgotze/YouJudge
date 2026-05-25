from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import SoftDeleteModel
import uuid


class Competition(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    ICON_CHOICES = [
        ('trophy-fill',       'Trophy'),
        ('star-fill',         'Star'),
        ('lightning-fill',    'Lightning'),
        ('award-fill',        'Award'),
        ('flag-fill',         'Flag'),
        ('rocket-fill',       'Rocket'),
        ('crown-fill',        'Crown'),
        ('shield-fill',       'Shield'),
        ('globe',             'Globe'),
        ('book-fill',         'Book'),
        ('palette-fill',      'Art'),
        ('cpu-fill',          'Technology'),
        ('fire',              'Fire'),
        ('gem',               'Gem'),
        ('heart-fill',        'Heart'),
        ('music-note-beamed', 'Music'),
    ]

    COLOR_CHOICES = [
        ('#ef4444', 'Red'),
        ('#f97316', 'Orange'),
        ('#f59e0b', 'Amber'),
        ('#eab308', 'Yellow'),
        ('#84cc16', 'Lime'),
        ('#10b981', 'Emerald'),
        ('#14b8a6', 'Teal'),
        ('#06b6d4', 'Cyan'),
        ('#3b82f6', 'Blue'),
        ('#084B83', 'Navy'),
        ('#6366f1', 'Indigo'),
        ('#8b5cf6', 'Violet'),
        ('#a855f7', 'Purple'),
        ('#ec4899', 'Pink'),
        ('#e11d48', 'Rose'),
        ('#6b7280', 'Gray'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_competitions',
        verbose_name=_('created by')
    )

    # Dates
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    icon = models.CharField(
        _('icon'), max_length=50,
        choices=ICON_CHOICES, default='trophy-fill'
    )
    color = models.CharField(
        _('color'), max_length=20, default='#084B83'
    )
    rules = models.TextField(_('rules'), blank=True)
    max_entries_per_participant = models.PositiveIntegerField(
        _('max entries per participant'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    max_score = models.PositiveIntegerField(
        _('max score per criteria'),
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text=''
    )

    class Meta:
        verbose_name = _('competition')
        verbose_name_plural = _('competitions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_upcoming(self):
        return self.status == 'draft'

    @property
    def is_ended(self):
        return self.status == 'closed'

    @property
    def scoring_is_open(self):
        return self.status == 'active'

    def sync_status(self):
        pass

    @property
    def icon_color(self):
        return self.color or '#084B83'

    @property
    def total_entries(self):
        return self.entries.count()

    @property
    def total_judges(self):
        return self.judge_assignments.filter(status='accepted').count()

    def can_user_edit(self, user):
        return self.created_by == user

    def can_user_judge(self, user):
        return self.judge_assignments.filter(
            judge=user,
            status='accepted'
        ).exists()


class JudgeAssignment(SoftDeleteModel):
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='judge_assignments',
        verbose_name=_('competition')
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judge_assignments',
        verbose_name=_('judge')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='invited'
    )
    invited_at = models.DateTimeField(_('invited at'), auto_now_add=True)
    responded_at = models.DateTimeField(_('responded at'), blank=True, null=True)

    class Meta:
        verbose_name = _('judge assignment')
        verbose_name_plural = _('judge assignments')
        ordering = ['-invited_at']
        indexes = [
            models.Index(fields=['competition', 'status']),
            models.Index(fields=['judge', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'judge'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_judge_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.judge.email} - {self.competition.title} ({self.status})'

    def accept(self):
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()

    def decline(self):
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()


class Criteria(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='criteria',
        verbose_name=_('competition')
    )
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    weight = models.PositiveIntegerField(
        _('weight'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Weight from 1 to 5, where 5 is most important')
    )
    order = models.PositiveIntegerField(_('order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('criterion')
        verbose_name_plural = _('criteria')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['competition', 'order']),
        ]

    def __str__(self):
        return f'{self.title} (Weight: {self.weight})'


class Category(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('competition')
    )
    name = models.CharField(_('name'), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'name'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_category_name',
            ),
        ]

    def __str__(self):
        return self.name


class PendingJudgeInvite(SoftDeleteModel):
    """Stores a judge invite for an email address that has no account yet."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email'))
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='pending_invites',
        verbose_name=_('competition')
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_pending_invites',
        verbose_name=_('invited by')
    )
    invited_at = models.DateTimeField(_('invited at'), auto_now_add=True)

    class Meta:
        verbose_name = _('pending judge invite')
        verbose_name_plural = _('pending judge invites')
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'competition'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_pending_invite',
            ),
        ]

    def __str__(self):
        return f'{self.email} → {self.competition.title}'


class Entry(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name=_('competition')
    )
    title = models.CharField(_('title'), max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entries',
        verbose_name=_('category')
    )
    participant_name = models.CharField(_('participant name'), max_length=255, blank=True)
    participant_email = models.EmailField(_('participant email'), blank=True)
    description = models.TextField(_('description'), blank=True)

    # File attachments
    file = models.FileField(_('file'), upload_to='entries/', blank=True, null=True)
    image = models.ImageField(_('image'), upload_to='entries/images/', blank=True, null=True)
    video_url = models.URLField(_('video URL'), blank=True)

    # Metadata
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='submitted_entries',
        verbose_name=_('submitted by'),
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('entry')
        verbose_name_plural = _('entries')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['competition', '-submitted_at']),
        ]

    def __str__(self):
        return f'{self.title} by {self.participant_name}'

    @property
    def total_score(self):
        from apps.scoring.models import Score
        scores = Score.objects.filter(entry=self).select_related('criteria')
        return round(sum(score.weighted_score for score in scores), 2)

    @property
    def average_score(self):
        from apps.scoring.models import Score
        scores = Score.objects.filter(entry=self)
        if not scores.exists():
            return 0
        return round(sum(score.score_value for score in scores) / scores.count(), 2)

    @property
    def total_judges(self):
        from apps.scoring.models import Score
        return Score.objects.filter(entry=self).values('judge').distinct().count()
