from django.db import migrations


def delete_orphaned_attempts(apps, schema_editor):
    """Delete any test attempts with null test_id before making the field non-nullable."""
    TestAttempt = apps.get_model('learning', 'TestAttempt')
    TestAttempt.objects.filter(test__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0031_testattempt_is_mixed_alter_testattempt_test'),
    ]

    operations = [
        migrations.RunPython(delete_orphaned_attempts, migrations.RunPython.noop),
    ]
