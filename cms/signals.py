"""
Signals to keep CMSTest in sync with learning.Test model.
This ensures that tests created in Wagtail CMS are available in the API.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cms.models import CMSTest, CMSQuestion, CMSAnswer
from learning.models import Test, Question, AnswerOption


@receiver(post_save, sender=CMSTest)
def sync_cms_test_to_test(sender, instance, created, **kwargs):
    """
    When a CMSTest is created or updated, sync it to the Test model.
    """
    # Check if corresponding Test exists
    test, test_created = Test.objects.get_or_create(
        title=instance.title,
        defaults={
            'description': instance.description,
            'passing_percentage': instance.passing_percentage,
            'time_limit_seconds': instance.time_limit_seconds,
            'max_attempts': instance.max_attempts,
            'shuffle_questions': instance.shuffle_questions,
            'shuffle_answers': instance.shuffle_answers,
        }
    )
    
    # If test already exists, update it
    if not test_created:
        test.description = instance.description
        test.passing_percentage = instance.passing_percentage
        test.time_limit_seconds = instance.time_limit_seconds
        test.max_attempts = instance.max_attempts
        test.shuffle_questions = instance.shuffle_questions
        test.shuffle_answers = instance.shuffle_answers
        test.save()
    
    # Store the test ID in CMSTest for reference (we'll need to add this field)
    # For now, we'll use title matching


@receiver(post_save, sender=CMSQuestion)
def sync_cms_question_to_question(sender, instance, created, **kwargs):
    """
    When a CMSQuestion is created or updated, sync it to the Question model.
    """
    # Find the corresponding Test
    try:
        test = Test.objects.get(title=instance.test.title)
    except Test.DoesNotExist:
        return
    
    # Check if corresponding Question exists
    # We'll match by test and text (not perfect but workable)
    question, question_created = Question.objects.get_or_create(
        test=test,
        text=instance.text,
        defaults={
            'question_type': instance.question_type,
            'order': instance.order,
        }
    )
    
    # If question already exists, update it
    if not question_created:
        question.question_type = instance.question_type
        question.order = instance.order
        question.save()


@receiver(post_save, sender=CMSAnswer)
def sync_cms_answer_to_answer_option(sender, instance, created, **kwargs):
    """
    When a CMSAnswer is created or updated, sync it to the AnswerOption model.
    """
    # Find the corresponding Question
    try:
        test = Test.objects.get(title=instance.question.test.title)
        question = Question.objects.get(test=test, text=instance.question.text)
    except (Test.DoesNotExist, Question.DoesNotExist):
        return
    
    # Use update_or_create to handle both creation and updates
    # Match by question and text (unique identifier for an answer)
    answer, answer_created = AnswerOption.objects.update_or_create(
        question=question,
        text=instance.text,
        defaults={
            'is_correct': instance.is_correct,
            'explanation': instance.explanation,
            'order': instance.order,
        }
    )


@receiver(post_delete, sender=CMSTest)
def delete_synced_test(sender, instance, **kwargs):
    """
    When a CMSTest is deleted, delete the corresponding Test.
    """
    try:
        test = Test.objects.get(title=instance.title)
        test.delete()
    except Test.DoesNotExist:
        pass


@receiver(post_delete, sender=CMSQuestion)
def delete_synced_question(sender, instance, **kwargs):
    """
    When a CMSQuestion is deleted, delete the corresponding Question.
    """
    try:
        test = Test.objects.get(title=instance.test.title)
        question = Question.objects.get(test=test, text=instance.text)
        question.delete()
    except (Test.DoesNotExist, Question.DoesNotExist):
        pass


@receiver(post_delete, sender=CMSAnswer)
def delete_synced_answer(sender, instance, **kwargs):
    """
    When a CMSAnswer is deleted, delete the corresponding AnswerOption.
    """
    try:
        test = Test.objects.get(title=instance.question.test.title)
        question = Question.objects.get(test=test, text=instance.question.text)
        answer = AnswerOption.objects.get(question=question, text=instance.text)
        answer.delete()
    except (Test.DoesNotExist, Question.DoesNotExist, AnswerOption.DoesNotExist):
        pass
