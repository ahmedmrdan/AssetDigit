from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add position to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='position',
            field=models.CharField(blank=True, max_length=100, verbose_name='Job Position/Title'),
        ),

        # Create CompanySettings singleton
        migrations.CreateModel(
            name='CompanySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('factory_name',       models.CharField(max_length=200, default='My Factory')),
                ('factory_name_ar',    models.CharField(max_length=200, blank=True)),
                ('location',           models.CharField(max_length=300, blank=True)),
                ('location_ar',        models.CharField(max_length=300, blank=True)),
                ('logo_text',          models.CharField(max_length=10, blank=True, default='🏭')),
                ('phone',              models.CharField(max_length=50, blank=True)),
                ('email',              models.EmailField(blank=True)),
                ('website',            models.CharField(max_length=200, blank=True)),
                ('welcome_message',    models.CharField(max_length=300, blank=True)),
                ('welcome_message_ar', models.CharField(max_length=300, blank=True)),
                ('updated_at',         models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Company Settings', 'verbose_name_plural': 'Company Settings'},
        ),
    ]
