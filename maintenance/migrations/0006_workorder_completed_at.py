from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0005_safety_permit'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='completed_at',
            field=models.DateTimeField(null=True, blank=True,
                                       verbose_name='Completed At (exact timestamp)'),
        ),
    ]
