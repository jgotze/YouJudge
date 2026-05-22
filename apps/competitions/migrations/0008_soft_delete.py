from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0007_add_total_max_score'),
    ]

    operations = [
        # ── Add deleted_at to every competition model ──────────────────────
        migrations.AddField(
            model_name='competition',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='judgeassignment',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='criteria',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='entry',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='pendingjudgeinvite',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),

        # ── Replace unique_together with partial UniqueConstraints ─────────
        # JudgeAssignment
        migrations.AlterUniqueTogether(
            name='judgeassignment',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='judgeassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['competition', 'judge'],
                name='unique_active_judge_assignment',
            ),
        ),

        # Category
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['competition', 'name'],
                name='unique_active_category_name',
            ),
        ),

        # PendingJudgeInvite
        migrations.AlterUniqueTogether(
            name='pendingjudgeinvite',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='pendingjudgeinvite',
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=['email', 'competition'],
                name='unique_active_pending_invite',
            ),
        ),
    ]
