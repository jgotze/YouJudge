from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import SoftDeleteModel
import uuid


class Score(SoftDeleteModel):
    """Model representing a judge's score for an entry on a specific criterion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name=_('judge')
    )
    entry = models.ForeignKey(
        'competitions.Entry',
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name=_('entry')
    )
    criteria = models.ForeignKey(
        'competitions.Criteria',
        on_delete=models.CASCADE,
        related_name='scores',
        verbose_name=_('criteria')
    )
    score_value = models.PositiveIntegerField(
        _('score value'),
        validators=[MinValueValidator(0)],
        help_text=_('Score from 0 to the competition max score')
    )
    weighted_score = models.FloatField(
        _('weighted score'),
        editable=False,
        default=0
    )
    comment = models.TextField(_('comment'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('score')
        verbose_name_plural = _('scores')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['judge', 'entry']),
            models.Index(fields=['entry', 'criteria']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['judge', 'entry', 'criteria'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_score',
            ),
        ]

    def __str__(self):
        return f'{self.judge.email} - {self.entry.title} - {self.criteria.title}: {self.score_value}/10'

    def clean(self):
        super().clean()
        from apps.competitions.models import JudgeAssignment
        if not JudgeAssignment.objects.filter(
            competition=self.entry.competition,
            judge=self.judge,
            status='accepted'
        ).exists():
            raise ValidationError(
                _('Judge must be assigned to this competition to score entries.')
            )
        if self.criteria.competition != self.entry.competition:
            raise ValidationError(
                _('Criteria must belong to the same competition as the entry.')
            )
        max_score = self.entry.competition.max_score
        if self.score_value is not None and self.score_value > max_score:
            raise ValidationError(
                _(f'Score cannot exceed the competition maximum of {max_score}.')
            )

    def calculate_weighted_score(self):
        return self.score_value * self.criteria.weight

    def save(self, *args, **kwargs):
        self.full_clean()
        self.weighted_score = self.calculate_weighted_score()
        super().save(*args, **kwargs)


class Leaderboard(SoftDeleteModel):
    """Model for caching leaderboard results."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='leaderboards',
        verbose_name=_('competition')
    )
    entry = models.ForeignKey(
        'competitions.Entry',
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name=_('entry')
    )
    total_weighted_score = models.FloatField(_('total weighted score'), default=0)
    rank = models.PositiveIntegerField(_('rank'), default=0)
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('leaderboard entry')
        verbose_name_plural = _('leaderboard entries')
        ordering = ['rank', '-total_weighted_score']
        indexes = [
            models.Index(fields=['competition', 'rank']),
            models.Index(fields=['competition', '-total_weighted_score']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'entry'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_leaderboard_entry',
            ),
        ]

    def __str__(self):
        return f'{self.entry.title} - Rank {self.rank} ({self.total_weighted_score})'

    @classmethod
    def update_leaderboard(cls, competition):
        from django.db.models import Sum, Count

        entries = competition.entries.annotate(
            computed_total_score=Sum('scores__weighted_score'),
            score_count=Count('scores')
        ).order_by('-computed_total_score', 'title')

        # Hard-delete existing cache rows — this is an internal rebuild, not a user action
        cls.all_objects.filter(competition=competition).delete()

        rank = 1
        for entry in entries:
            if entry.computed_total_score is not None:
                cls.objects.create(
                    competition=competition,
                    entry=entry,
                    total_weighted_score=entry.computed_total_score or 0,
                    rank=rank
                )
                rank += 1


class JudgeProgress(SoftDeleteModel):
    """Model to track judge's progress in scoring a competition."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judge_progress',
        verbose_name=_('judge')
    )
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='judge_progress',
        verbose_name=_('competition')
    )
    total_entries = models.PositiveIntegerField(_('total entries'), default=0)
    scored_entries = models.PositiveIntegerField(_('scored entries'), default=0)
    progress_percentage = models.FloatField(_('progress percentage'), default=0)
    last_scored_at = models.DateTimeField(_('last scored at'), blank=True, null=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('judge progress')
        verbose_name_plural = _('judge progress')
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['judge', 'competition'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_active_judge_progress',
            ),
        ]

    def __str__(self):
        return f'{self.judge.email} - {self.competition.title}: {self.progress_percentage}%'

    @classmethod
    def update_progress(cls, judge, competition):
        from django.utils import timezone

        total_entries = competition.entries.count()
        total_criteria = competition.criteria.count()

        if total_entries == 0 or total_criteria == 0:
            progress_percentage = 0
            scored_entries = 0
        else:
            scored_entries = 0
            for entry in competition.entries.all():
                entry_scores = Score.objects.filter(
                    judge=judge,
                    entry=entry
                ).values('criteria').distinct().count()
                if entry_scores == total_criteria:
                    scored_entries += 1
            progress_percentage = (scored_entries / total_entries) * 100

        last_score = Score.objects.filter(
            judge=judge,
            entry__competition=competition
        ).order_by('-created_at').first()

        last_scored_at = last_score.created_at if last_score else None

        # Use all_objects so a soft-deleted progress record is restored rather than
        # triggering a unique constraint violation when a new one is created.
        progress, created = cls.all_objects.update_or_create(
            judge=judge,
            competition=competition,
            defaults={
                'total_entries': total_entries,
                'scored_entries': scored_entries,
                'progress_percentage': progress_percentage,
                'last_scored_at': last_scored_at,
                'deleted_at': None,
            }
        )

        return progress
