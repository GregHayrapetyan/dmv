# Generated migration to remove is_demo field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0021_test_vehicles'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='test',
            name='learning_te_is_demo_76ff88_idx',
        ),
        migrations.RemoveField(
            model_name='test',
            name='is_demo',
        ),
    ]
