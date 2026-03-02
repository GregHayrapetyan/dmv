from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0032_cleanup_mixed_attempts'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testattempt',
            name='is_mixed',
        ),
        migrations.AlterField(
            model_name='testattempt',
            name='test',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='attempts',
                to='learning.test',
            ),
        ),
    ]
