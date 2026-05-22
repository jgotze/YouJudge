from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scoring', '0003_alter_score_score_value'),
        ('competitions', '0008_soft_delete'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Add deleted_at to every scoring model ──────────────────────────
        migrations.AddField(
            model_name='score',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='leaderboard',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='judgeprogress',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),

        # ── Replace unique_together with partial UniqueConstraints ─────────
        # Score
        migrations.AlterUniqueTogether(
            name='score',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='score',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['judge', 'entry', 'criteria'],
                name='unique_active_score',
            ),
        ),

        # Leaderboard
        migrations.AlterUniqueTogether(
            name='leaderboard',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='leaderboard',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['competition', 'entry'],
                name='unique_active_leaderboard_entry',
            ),
        ),

        # JudgeProgress
        migrations.AlterUniqueTogether(
            name='judgeprogress',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='judgeprogress',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['judge', 'competition'],
                name='unique_active_judge_progress',
            ),
        ),
    ]
