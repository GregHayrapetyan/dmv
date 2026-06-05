"""
Signals to keep CMSTest in sync with learning.Test model.
This ensures that tests created in Wagtail CMS are available in the API.
"""
import io
import os

from django.conf import settings
from django.core.files.base import File, ContentFile
from django.db import models, transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from PIL import Image as PILImage
from wagtail.images.models import Image as WagtailImageModel

from cms.models import CMSTest, CMSQuestion, CMSAnswer
from learning.models import Test, Question, AnswerOption

MAX_DIMENSION = getattr(settings, 'IMAGE_MAX_DIMENSION', 800)


def _resize_image_if_needed(image_file, max_dim=MAX_DIMENSION):
    """
    Resize an image so that neither width nor height exceeds max_dim.
    Returns (resized_content_file, was_resized) or (None, False) on error.
    """
    try:
        img = PILImage.open(image_file)
        original_format = img.format or 'PNG'
        w, h = img.size
        if w <= max_dim and h <= max_dim:
            return None, False
        # Calculate new dimensions preserving aspect ratio
        ratio = min(max_dim / w, max_dim / h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, PILImage.LANCZOS)
        # Save to buffer using the original format
        buf = io.BytesIO()
        if img.mode in ('RGBA', 'P') and original_format == 'JPEG':
            img = img.convert('RGB')
        elif img.mode == 'P' and original_format == 'WEBP':
            img = img.convert('RGBA')
        img.save(buf, format=original_format, quality=85)
        buf.seek(0)
        return ContentFile(buf.read()), True
    except Exception:
        return None, False


@receiver(post_save, sender=WagtailImageModel)
def resize_wagtail_image_on_upload(sender, instance, created, **kwargs):
    """
    Auto-resize Wagtail images to max IMAGE_MAX_DIMENSION px on upload.
    """
    if not created:
        return
    try:
        file_field = instance.file
        file_field.open('rb')
        img = PILImage.open(file_field)
        original_format = img.format or 'PNG'
        w, h = img.size
        if w <= MAX_DIMENSION and h <= MAX_DIMENSION:
            file_field.close()
            return
        # Resize
        ratio = min(MAX_DIMENSION / w, MAX_DIMENSION / h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, PILImage.LANCZOS)
        buf = io.BytesIO()
        if img.mode in ('RGBA', 'P') and original_format == 'JPEG':
            img = img.convert('RGB')
        elif img.mode == 'P' and original_format == 'WEBP':
            img = img.convert('RGBA')
        img.save(buf, format=original_format, quality=85)
        buf.seek(0)
        # Save resized image back, disconnect signal to avoid recursion
        filename = os.path.basename(file_field.name)
        file_field.close()
        post_save.disconnect(resize_wagtail_image_on_upload, sender=WagtailImageModel)
        try:
            with transaction.atomic():
                instance.file.save(filename, ContentFile(buf.read()), save=False)
                instance.width = new_size[0]
                instance.height = new_size[1]
                instance.file_size = instance.file.size
                instance.save()
        finally:
            post_save.connect(resize_wagtail_image_on_upload, sender=WagtailImageModel)
    except Exception:
        pass


def _sync_filefield(source_field, target_obj, field_name):
    """Sync a Django FileField from CMS model to target model."""
    target_field = getattr(target_obj, field_name)
    if source_field:
        try:
            src_name = os.path.basename(source_field.name)
            # Skip if already the same file
            if target_field and os.path.basename(target_field.name) == src_name:
                return
            target_field.save(src_name, File(source_field), save=True)
        except Exception:
            pass
    else:
        if target_field:
            setattr(target_obj, field_name, None)
            target_obj.save()


def _sync_wagtail_image_to_imagefield(cms_image, target_obj, field_name='image'):
    """Copy a Wagtail Image file into a Django ImageField on target_obj, resized to max dimension."""
    target_field = getattr(target_obj, field_name)
    if cms_image:
        try:
            wagtail_file = cms_image.file
            filename = os.path.basename(wagtail_file.name)
            # Skip copy if the target already has an image with the same filename
            if target_field and os.path.basename(target_field.name) == filename:
                return
            # Resize before saving to the target field
            wagtail_file.open('rb')
            resized, was_resized = _resize_image_if_needed(wagtail_file)
            if was_resized and resized:
                target_field.save(filename, resized, save=True)
            else:
                wagtail_file.open('rb')
                target_field.save(filename, File(wagtail_file), save=True)
        except Exception:
            pass
    else:
        if target_field:
            setattr(target_obj, field_name, None)
            target_obj.save()


@receiver(post_save, sender=CMSTest)
def sync_cms_test_to_test(sender, instance, created, **kwargs):
    """
    When a CMSTest is created or updated, sync it to the Test model.
    """
    # Look up by stable FK link first
    try:
        test = Test.objects.get(cms_test=instance)
    except Test.DoesNotExist:
        test = None

    if test is None:
        test = Test.objects.create(
            cms_test=instance,
            title=instance.title,
            description=instance.description,
            passing_percentage=instance.passing_percentage,
            time_limit_seconds=instance.time_limit_seconds,
            max_attempts=instance.max_attempts,
            shuffle_questions=instance.shuffle_questions,
            shuffle_answers=instance.shuffle_answers,
            order=instance.order,
            is_demo=instance.is_demo,
            mixed_question_count=instance.mixed_question_count,
            title_ru=instance.title_ru,
            description_ru=instance.description_ru,
            title_hy=instance.title_hy,
            description_hy=instance.description_hy,
            title_hi=instance.title_hi,
            description_hi=instance.description_hi,
            title_es=instance.title_es,
            description_es=instance.description_es,
            title_zh=instance.title_zh,
            description_zh=instance.description_zh,
        )
    else:
        test.title = instance.title
        test.description = instance.description
        test.passing_percentage = instance.passing_percentage
        test.time_limit_seconds = instance.time_limit_seconds
        test.max_attempts = instance.max_attempts
        test.shuffle_questions = instance.shuffle_questions
        test.shuffle_answers = instance.shuffle_answers
        test.order = instance.order
        test.is_demo = instance.is_demo
        test.mixed_question_count = instance.mixed_question_count
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
    
    # Sync image from Wagtail Image to Django ImageField (per language)
    _sync_wagtail_image_to_imagefield(instance.image, test, 'image')
    _sync_wagtail_image_to_imagefield(instance.image_ru, test, 'image_ru')
    _sync_wagtail_image_to_imagefield(instance.image_hy, test, 'image_hy')
    _sync_wagtail_image_to_imagefield(instance.image_hi, test, 'image_hi')
    _sync_wagtail_image_to_imagefield(instance.image_es, test, 'image_es')
    _sync_wagtail_image_to_imagefield(instance.image_zh, test, 'image_zh')


@receiver(post_save, sender=CMSQuestion)
def sync_cms_question_to_question(sender, instance, created, **kwargs):
    """
    When a CMSQuestion is created or updated, sync it to the Question model.
    """
    # Find the corresponding Test via stable FK
    try:
        test = Test.objects.get(cms_test=instance.test)
    except Test.DoesNotExist:
        return
    
    # Look up by stable FK link
    try:
        question = Question.objects.get(cms_question=instance)
    except Question.DoesNotExist:
        question = None

    if question is None:
        question = Question.objects.create(
            cms_question=instance,
            test=test,
            text=instance.text,
            question_type=instance.question_type,
            explanation=instance.explanation,
            order=instance.order,
            text_ru=instance.text_ru,
            explanation_ru=instance.explanation_ru,
            text_hy=instance.text_hy,
            explanation_hy=instance.explanation_hy,
            text_hi=instance.text_hi,
            explanation_hi=instance.explanation_hi,
            text_es=instance.text_es,
            explanation_es=instance.explanation_es,
            text_zh=instance.text_zh,
            explanation_zh=instance.explanation_zh,
        )
    else:
        question.test = test
        question.text = instance.text
        question.question_type = instance.question_type
        question.explanation = instance.explanation
        question.order = instance.order
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
    
    # Sync image from Wagtail Image to Django ImageField
    _sync_wagtail_image_to_imagefield(instance.image, question)
    
    # Sync video file
    _sync_filefield(instance.video, question, 'video')


@receiver(post_save, sender=CMSAnswer)
def sync_cms_answer_to_answer_option(sender, instance, created, **kwargs):
    """
    When a CMSAnswer is created or updated, sync it to the AnswerOption model.
    """
    # Find the corresponding Question via stable FK
    try:
        question = Question.objects.get(cms_question=instance.question)
    except Question.DoesNotExist:
        return
    
    # Look up by stable FK link
    try:
        answer = AnswerOption.objects.get(cms_answer=instance)
        answer.question = question
        answer.text = instance.text
        answer.is_correct = instance.is_correct
        answer.order = instance.order
        answer.text_ru = instance.text_ru
        answer.text_hy = instance.text_hy
        answer.text_hi = instance.text_hi
        answer.text_es = instance.text_es
        answer.text_zh = instance.text_zh
        answer.save()
    except AnswerOption.DoesNotExist:
        AnswerOption.objects.create(
            cms_answer=instance,
            question=question,
            text=instance.text,
            is_correct=instance.is_correct,
            order=instance.order,
            text_ru=instance.text_ru,
            text_hy=instance.text_hy,
            text_hi=instance.text_hi,
            text_es=instance.text_es,
            text_zh=instance.text_zh,
        )


@receiver(pre_delete, sender=CMSTest)
def delete_synced_test(sender, instance, **kwargs):
    """
    When a CMSTest is deleted, delete the corresponding Test.

    Uses pre_delete (not post_delete) because Test.cms_test has
    on_delete=SET_NULL: by the time post_delete fires, Test.cms_test_id
    has already been nulled and the filter would match no rows.
    """
    Test.objects.filter(cms_test=instance).delete()


@receiver(pre_delete, sender=CMSQuestion)
def delete_synced_question(sender, instance, **kwargs):
    """
    When a CMSQuestion is deleted, delete the corresponding Question.

    Uses pre_delete (not post_delete) because Question.cms_question has
    on_delete=SET_NULL: by the time post_delete fires, Question.cms_question_id
    has already been nulled and the filter would match no rows.
    """
    Question.objects.filter(cms_question=instance).delete()


@receiver(pre_delete, sender=CMSAnswer)
def delete_synced_answer(sender, instance, **kwargs):
    """
    When a CMSAnswer is deleted, delete the corresponding AnswerOption.

    Uses pre_delete (not post_delete) because AnswerOption.cms_answer has
    on_delete=SET_NULL: by the time post_delete fires, AnswerOption.cms_answer_id
    has already been nulled and the filter would match no rows.
    """
    AnswerOption.objects.filter(cms_answer=instance).delete()
