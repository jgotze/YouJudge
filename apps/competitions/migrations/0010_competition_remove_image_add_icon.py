from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0009_remove_total_max_score'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competition',
            name='image',
        ),
        migrations.AddField(
            model_name='competition',
            name='icon',
            field=models.CharField(
                choices=[
                    ('trophy-fill', 'Trophy'),
                    ('star-fill', 'Star'),
                    ('lightning-fill', 'Lightning'),
                    ('award-fill', 'Award'),
                    ('flag-fill', 'Flag'),
                    ('rocket-fill', 'Rocket'),
                    ('crown-fill', 'Crown'),
                    ('shield-fill', 'Shield'),
                    ('globe', 'Globe'),
                    ('book-fill', 'Book'),
                    ('palette-fill', 'Art'),
                    ('cpu-fill', 'Technology'),
                    ('fire', 'Fire'),
                    ('gem', 'Gem'),
                    ('heart-fill', 'Heart'),
                    ('music-note-beamed', 'Music'),
                ],
                default='trophy-fill',
                max_length=50,
                verbose_name='icon',
            ),
        ),
    ]
