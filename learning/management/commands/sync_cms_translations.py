"""
Management command to sync all CMS translations to learning models.
Run this after adding translation fields to re-sync existing data.
"""
from django.core.management.base import BaseCommand
from cms.models import CMSTest, CMSQuestion, CMSAnswer
from learning.models import Test, Question, AnswerOption


class Command(BaseCommand):
    help = 'Sync all CMS translations to learning models'

    def handle(self, *args, **options):
        self.stdout.write('Syncing CMS translations to learning models...\n')
        
        # Sync Tests
        tests_synced = 0
        for cms_test in CMSTest.objects.all():
            try:
                test = Test.objects.get(title=cms_test.title)
                # Update translation fields
                test.title_ru = cms_test.title_ru
                test.description_ru = cms_test.description_ru
                test.title_hy = cms_test.title_hy
                test.description_hy = cms_test.description_hy
                test.title_hi = cms_test.title_hi
                test.description_hi = cms_test.description_hi
                test.title_es = cms_test.title_es
                test.description_es = cms_test.description_es
                test.title_zh = cms_test.title_zh
                test.description_zh = cms_test.description_zh
                # Also sync other fields
                test.description = cms_test.description
                test.passing_percentage = cms_test.passing_percentage
                test.time_limit_seconds = cms_test.time_limit_seconds
                test.max_attempts = cms_test.max_attempts
                test.shuffle_questions = cms_test.shuffle_questions
                test.shuffle_answers = cms_test.shuffle_answers
                test.save()
                tests_synced += 1
                self.stdout.write(f'  Synced test: {cms_test.title}')
            except Test.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  Test not found: {cms_test.title} - creating...')
                )
                Test.objects.create(
                    title=cms_test.title,
                    description=cms_test.description,
                    passing_percentage=cms_test.passing_percentage,
                    time_limit_seconds=cms_test.time_limit_seconds,
                    max_attempts=cms_test.max_attempts,
                    shuffle_questions=cms_test.shuffle_questions,
                    shuffle_answers=cms_test.shuffle_answers,
                    title_ru=cms_test.title_ru,
                    description_ru=cms_test.description_ru,
                    title_hy=cms_test.title_hy,
                    description_hy=cms_test.description_hy,
                    title_hi=cms_test.title_hi,
                    description_hi=cms_test.description_hi,
                    title_es=cms_test.title_es,
                    description_es=cms_test.description_es,
                    title_zh=cms_test.title_zh,
                    description_zh=cms_test.description_zh,
                )
                tests_synced += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSynced {tests_synced} tests'))
        
        # Sync Questions
        questions_synced = 0
        for cms_question in CMSQuestion.objects.all():
            try:
                test = Test.objects.get(title=cms_question.test.title)
                question, created = Question.objects.get_or_create(
                    test=test,
                    text=cms_question.text,
                    defaults={
                        'question_type': cms_question.question_type,
                        'explanation': cms_question.explanation,
                        'order': cms_question.order,
                    }
                )
                # Update translation fields
                question.text_ru = cms_question.text_ru
                question.explanation_ru = cms_question.explanation_ru
                question.text_hy = cms_question.text_hy
                question.explanation_hy = cms_question.explanation_hy
                question.text_hi = cms_question.text_hi
                question.explanation_hi = cms_question.explanation_hi
                question.text_es = cms_question.text_es
                question.explanation_es = cms_question.explanation_es
                question.text_zh = cms_question.text_zh
                question.explanation_zh = cms_question.explanation_zh
                # Also sync other fields
                question.question_type = cms_question.question_type
                question.explanation = cms_question.explanation
                question.order = cms_question.order
                question.save()
                questions_synced += 1
            except Test.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  Test not found for question: {cms_question.text[:50]}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'Synced {questions_synced} questions'))
        
        # Sync Answers - match by order within question
        answers_synced = 0
        answers_skipped = 0
        for cms_answer in CMSAnswer.objects.all():
            try:
                test = Test.objects.get(title=cms_answer.question.test.title)
                question = Question.objects.get(test=test, text=cms_answer.question.text)
                # Try to find existing answer by order (more reliable than text)
                try:
                    answer = AnswerOption.objects.get(question=question, order=cms_answer.order)
                    # Update translation fields only
                    answer.text_ru = cms_answer.text_ru
                    answer.text_hy = cms_answer.text_hy
                    answer.text_hi = cms_answer.text_hi
                    answer.text_es = cms_answer.text_es
                    answer.text_zh = cms_answer.text_zh
                    answer.save(update_fields=['text_ru', 'text_hy', 'text_hi', 'text_es', 'text_zh'])
                    answers_synced += 1
                except AnswerOption.DoesNotExist:
                    # Try by text as fallback
                    try:
                        answer = AnswerOption.objects.get(question=question, text=cms_answer.text)
                        answer.text_ru = cms_answer.text_ru
                        answer.text_hy = cms_answer.text_hy
                        answer.text_hi = cms_answer.text_hi
                        answer.text_es = cms_answer.text_es
                        answer.text_zh = cms_answer.text_zh
                        answer.save(update_fields=['text_ru', 'text_hy', 'text_hi', 'text_es', 'text_zh'])
                        answers_synced += 1
                    except AnswerOption.DoesNotExist:
                        answers_skipped += 1
                except AnswerOption.MultipleObjectsReturned:
                    answers_skipped += 1
            except (Test.DoesNotExist, Question.DoesNotExist):
                answers_skipped += 1
        
        self.stdout.write(self.style.SUCCESS(f'Synced {answers_synced} answers'))
        self.stdout.write(self.style.SUCCESS('\nSync complete!'))
