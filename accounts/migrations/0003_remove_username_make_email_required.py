# Generated manually

from django.db import migrations, models
import django.core.validators


def populate_empty_emails(apps, schema_editor):
    """Populate empty emails with a placeholder based on username or ID"""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.filter(email__isnull=True) | User.objects.filter(email=''):
        if user.username:
            user.email = f"{user.username}@placeholder.local"
        else:
            user.email = f"user{user.id}@placeholder.local"
        user.save(update_fields=['email'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_emailotp'),
    ]

    operations = [
        # Step 1: Populate empty emails
        migrations.RunPython(populate_empty_emails, migrations.RunPython.noop),
        
        # Step 2: Make email non-nullable
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True),
        ),
        
        # Step 3: Remove username field
        migrations.RemoveField(
            model_name='user',
            name='username',
        ),
    ]
