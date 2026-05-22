from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0008_soft_delete'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competition',
            name='total_max_score',
        ),
    ]
