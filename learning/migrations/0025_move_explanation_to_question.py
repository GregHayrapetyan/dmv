# Generated migration to move explanation from AnswerOption to Question

from django.db import migrations, models


def move_explanations_forward(apps, schema_editor):
    """Move explanations from correct answers to their questions."""
    Question = apps.get_model('learning', 'Question')
    AnswerOption = apps.get_model('learning', 'AnswerOption')
    
    for question in Question.objects.all():
        # Find the correct answer with an explanation
        correct_answer = question.answer_options.filter(
            is_correct=True
        ).exclude(explanation='').first()
        
        if correct_answer and correct_answer.explanation:
            question.explanation = correct_answer.explanation
            question.save(update_fields=['explanation'])


def move_explanations_backward(apps, schema_editor):
    """Move explanations back from questions to correct answers."""
    Question = apps.get_model('learning', 'Question')
    AnswerOption = apps.get_model('learning', 'AnswerOption')
    
    for question in Question.objects.exclude(explanation=''):
        # Find the correct answer
        correct_answer = question.answer_options.filter(is_correct=True).first()
        
        if correct_answer:
            correct_answer.explanation = question.explanation
            correct_answer.save(update_fields=['explanation'])


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0023_remove_weight_from_question'),
    ]

    operations = [
        # Add explanation field to Question
        migrations.AddField(
            model_name='question',
            name='explanation',
            field=models.TextField(blank=True, help_text='Explanation for the correct answer'),
        ),
        # Move data from AnswerOption.explanation to Question.explanation
        migrations.RunPython(move_explanations_forward, move_explanations_backward),
        # Remove explanation field from AnswerOption
        migrations.RemoveField(
            model_name='answeroption',
            name='explanation',
        ),
    ]
