# Generated manually on 2025-12-18

from django.db import migrations, models


def migrate_test_attempt_data(apps, schema_editor):
    """
    Migrate existing TestAttempt data:
    - correct_answers = score (already renamed)
    - incorrect_answers = total_points - score
    - questions_count = total_points (already renamed)
    """
    TestAttempt = apps.get_model('learning', 'TestAttempt')
    
    for attempt in TestAttempt.objects.all():
        # incorrect_answers was renamed from total_points, so we need to calculate it
        # correct_answers was renamed from score
        # questions_count was renamed from total_points
        attempt.incorrect_answers = attempt.questions_count - attempt.correct_answers
        attempt.save(update_fields=['incorrect_answers'])


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0011_remove_lesson_from_test'),
    ]

    operations = [
        # Step 1: Remove old constraint on Question.points
        migrations.RemoveConstraint(
            model_name='question',
            name='question_points_positive',
        ),
        
        # Step 2: Remove Question.points field (not needed anymore)
        migrations.RemoveField(
            model_name='question',
            name='points',
        ),
        
        # Step 3: Rename TestAttempt.score to TestAttempt.correct_answers
        migrations.RenameField(
            model_name='testattempt',
            old_name='score',
            new_name='correct_answers',
        ),
        
        # Step 4: Rename TestAttempt.total_points to TestAttempt.questions_count
        migrations.RenameField(
            model_name='testattempt',
            old_name='total_points',
            new_name='questions_count',
        ),
        
        # Step 5: Add TestAttempt.incorrect_answers field
        migrations.AddField(
            model_name='testattempt',
            name='incorrect_answers',
            field=models.PositiveIntegerField(default=0),
        ),
        
        # Step 6: Migrate data to calculate incorrect_answers
        migrations.RunPython(migrate_test_attempt_data, migrations.RunPython.noop),
    ]
