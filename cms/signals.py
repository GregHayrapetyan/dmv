"""
Signals to keep CMSTest in sync with learning.Test model.
This ensures that tests created in Wagtail CMS are available in the API.
"""
from django.db import models
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
            # Translation fields
            'title_ru': instance.title_ru,
            'description_ru': instance.description_ru,
            'title_hy': instance.title_hy,
            'description_hy': instance.description_hy,
            'title_hi': instance.title_hi,
            'description_hi': instance.description_hi,
            'title_es': instance.title_es,
            'description_es': instance.description_es,
            'title_zh': instance.title_zh,
            'description_zh': instance.description_zh,
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
        # Translation fields
        test.title_ru = instance.title_ru
        test.description_ru = instance.description_ru
        test.title_hy = instance.title_hy
        test.description_hy = instance.description_hy
        test.title_hi = instance.title_hi
        test.description_hi = instance.description_hi
        test.title_es = instance.title_es
        test.description_es = instance.description_es
        test.title_zh = instance.title_zh
        test.description_zh = instance.description_zh
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
            'explanation': instance.explanation,
            'order': instance.order,
            # Translation fields
            'text_ru': instance.text_ru,
            'explanation_ru': instance.explanation_ru,
            'text_hy': instance.text_hy,
            'explanation_hy': instance.explanation_hy,
            'text_hi': instance.text_hi,
            'explanation_hi': instance.explanation_hi,
            'text_es': instance.text_es,
            'explanation_es': instance.explanation_es,
            'text_zh': instance.text_zh,
            'explanation_zh': instance.explanation_zh,
        }
    )
    
    # If question already exists, update it
    if not question_created:
        question.question_type = instance.question_type
        question.explanation = instance.explanation
        question.order = instance.order
        # Translation fields
        question.text_ru = instance.text_ru
        question.explanation_ru = instance.explanation_ru
        question.text_hy = instance.text_hy
        question.explanation_hy = instance.explanation_hy
        question.text_hi = instance.text_hi
        question.explanation_hi = instance.explanation_hi
        question.text_es = instance.text_es
        question.explanation_es = instance.explanation_es
        question.text_zh = instance.text_zh
        question.explanation_zh = instance.explanation_zh
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
    
    # First try to find existing answer by question and text
    try:
        answer = AnswerOption.objects.get(question=question, text=instance.text)
        # Update existing answer (order can stay as-is to avoid constraint issues)
        answer.is_correct = instance.is_correct
        answer.text_ru = instance.text_ru
        answer.text_hy = instance.text_hy
        answer.text_hi = instance.text_hi
        answer.text_es = instance.text_es
        answer.text_zh = instance.text_zh
        answer.save()
    except AnswerOption.DoesNotExist:
        # Create new answer - find next available order to avoid constraint violation
        max_order = AnswerOption.objects.filter(question=question).aggregate(
            max_order=models.Max('order')
        )['max_order']
        next_order = (max_order or -1) + 1
        
        AnswerOption.objects.create(
            question=question,
            text=instance.text,
            is_correct=instance.is_correct,
            order=next_order,
            text_ru=instance.text_ru,
            text_hy=instance.text_hy,
            text_hi=instance.text_hi,
            text_es=instance.text_es,
            text_zh=instance.text_zh,
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
