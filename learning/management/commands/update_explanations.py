import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from learning.models import Test, Question, AnswerOption


class Command(BaseCommand):
    help = 'Update existing questions with explanations from questions.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='questions.json',
            help='Path to the questions JSON file (default: questions.json)',
        )

    def handle(self, *args, **options):
        file_path = options.get('file')

        # Load JSON data
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File "{file_path}" not found')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in file "{file_path}"')

        # Handle both list and single object formats
        if isinstance(data, list):
            state_objects = data
        else:
            state_objects = [data]

        stats = {
            'questions_processed': 0,
            'questions_updated': 0,
            'questions_not_found': 0,
        }

        # Process each state object
        for state_data in state_objects:
            state_name = state_data.get('state')
            if not state_name:
                continue

            self.stdout.write(f'\nProcessing state: {state_name}')

            questions_data = state_data.get('questions', [])
            
            for q_data in questions_data:
                question_text = q_data.get('question')
                explanation = q_data.get('explanation', '')
                correct_index = q_data.get('correct')
                
                if not question_text or not explanation:
                    continue

                # Find the question by text
                questions = Question.objects.filter(text=question_text)
                
                if not questions.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Question not found: {question_text[:50]}...'
                        )
                    )
                    stats['questions_not_found'] += 1
                    continue

                # Update all matching questions (in case of duplicates across tests)
                for question in questions:
                    stats['questions_processed'] += 1
                    
                    # Update explanation if it's different
                    if question.explanation != explanation:
                        with transaction.atomic():
                            question.explanation = explanation
                            question.save()
                            stats['questions_updated'] += 1
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  Updated explanation for: {question_text[:50]}...'
                                )
                            )

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Update completed!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Questions processed: {stats["questions_processed"]}')
        self.stdout.write(f'Questions updated: {stats["questions_updated"]}')
        self.stdout.write(f'Questions not found: {stats["questions_not_found"]}')
        self.stdout.write('='*60)
