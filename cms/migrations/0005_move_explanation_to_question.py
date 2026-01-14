# Generated migration to move explanation from CMSAnswer to CMSQuestion

from django.db import migrations, models


def move_explanations_forward(apps, schema_editor):
    """Move explanations from correct answers to their questions."""
    CMSQuestion = apps.get_model('cms', 'CMSQuestion')
    CMSAnswer = apps.get_model('cms', 'CMSAnswer')
    
    for question in CMSQuestion.objects.all():
        # Find the correct answer with an explanation
        correct_answer = question.answers.filter(
            is_correct=True
        ).exclude(explanation='').first()
        
        if correct_answer and correct_answer.explanation:
            question.explanation = correct_answer.explanation
            question.save(update_fields=['explanation'])


def move_explanations_backward(apps, schema_editor):
    """Move explanations back from questions to correct answers."""
    CMSQuestion = apps.get_model('cms', 'CMSQuestion')
    CMSAnswer = apps.get_model('cms', 'CMSAnswer')
    
    for question in CMSQuestion.objects.exclude(explanation=''):
        # Find the correct answer
        correct_answer = question.answers.filter(is_correct=True).first()
        
        if correct_answer:
            correct_answer.explanation = question.explanation
            correct_answer.save(update_fields=['explanation'])


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_alter_cmsanswer_question_alter_cmsquestion_test'),
    ]

    operations = [
        # Add explanation field to CMSQuestion
        migrations.AddField(
            model_name='cmsquestion',
            name='explanation',
            field=models.TextField(blank=True, help_text='Explanation for the correct answer'),
        ),
        # Move data from CMSAnswer.explanation to CMSQuestion.explanation
        migrations.RunPython(move_explanations_forward, move_explanations_backward),
        # Remove explanation field from CMSAnswer
        migrations.RemoveField(
            model_name='cmsanswer',
            name='explanation',
        ),
    ]
