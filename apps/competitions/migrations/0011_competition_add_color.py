from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0010_competition_remove_image_add_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='color',
            field=models.CharField(default='#084B83', max_length=20, verbose_name='color'),
        ),
    ]
