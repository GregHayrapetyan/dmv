import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from learning.models import Test, Question, AnswerOption
from onboarding.models import State


class Command(BaseCommand):
    help = 'Import questions from questions.json file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--state',
            type=str,
            help='State name to import questions for (e.g., "California")',
        )
        parser.add_argument(
            '--file',
            type=str,
            default='questions.json',
            help='Path to the questions JSON file (default: questions.json)',
        )

    def handle(self, *args, **options):
        state_filter = options.get('state')
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

        # Process each state object
        for state_data in state_objects:
            self._process_state(state_data, state_filter)

    def _process_state(self, data, state_filter):
        """Process a single state's questions."""
        # Get state from JSON
        state_name = data.get('state')
        if not state_name:
            self.stdout.write(
                self.style.WARNING('Skipping object without "state" field')
            )
            return

        # Check if we should process this state
        if state_filter and state_name != state_filter:
            self.stdout.write(
                self.style.WARNING(
                    f'Skipping state "{state_name}" (filtering for "{state_filter}")'
                )
            )
            return

        # Get or create the state
        state, created = State.objects.get_or_create(name=state_name)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created new state: {state_name}')
            )
        else:
            self.stdout.write(f'Using existing state: {state_name}')

        questions_data = data.get('questions', [])
        if not questions_data:
            self.stdout.write(
                self.style.WARNING(f'No questions found for state "{state_name}"')
            )
            return

        # Group questions by category
        questions_by_category = {}
        for q_data in questions_data:
            category = q_data.get('category')
            if category:
                if category not in questions_by_category:
                    questions_by_category[category] = []
                questions_by_category[category].append(q_data)

        # Statistics
        stats = {
            'tests_created': 0,
            'tests_updated': 0,
            'questions_created': 0,
            'questions_skipped': 0,
            'answers_created': 0,
        }

        # Process each category
        for category, questions in questions_by_category.items():
            with transaction.atomic():
                # Get or create test for this category
                test, test_created = Test.objects.get_or_create(
                    title=category.replace('_', ' ').title(),
                    defaults={
                        'description': f'Test for {category.replace("_", " ").title()}',
                        'passing_percentage': 100,
                        'shuffle_questions': True,
                        'shuffle_answers': True,
                    }
                )

                # Add state to test if not already added
                if state not in test.states.all():
                    test.states.add(state)
                    stats['tests_updated'] += 1

                if test_created:
                    stats['tests_created'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created test: {test.title}')
                    )
                else:
                    self.stdout.write(f'Using existing test: {test.title}')

                # Process questions for this test
                for q_data in questions:
                    question_text = q_data.get('question')
                    if not question_text:
                        continue

                    # Check if question already exists (by text)
                    existing_question = Question.objects.filter(
                        test=test,
                        text=question_text
                    ).first()

                    if existing_question:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Skipping duplicate question: {question_text[:50]}...'
                            )
                        )
                        stats['questions_skipped'] += 1
                        continue

                    # Get the next order number for this test
                    max_order = Question.objects.filter(test=test).count()
                    
                    # Create question
                    question = Question.objects.create(
                        test=test,
                        text=question_text,
                        question_type=Question.QuestionType.MULTIPLE_CHOICE,
                        order=max_order + 1
                    )

                    # Handle video and image links if provided
                    video_link = q_data.get('video_link')
                    image_link = q_data.get('image_link')
                    # Note: These are URLs, but the model expects file fields
                    # You may need to download and save these files separately
                    # For now, we'll just note them in the output
                    if video_link:
                        self.stdout.write(
                            self.style.NOTICE(
                                f'    Note: Question has video link: {video_link}'
                            )
                        )
                    if image_link:
                        self.stdout.write(
                            self.style.NOTICE(
                                f'    Note: Question has image link: {image_link}'
                            )
                        )

                    stats['questions_created'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Created question #{question.order}: {question_text[:50]}...'
                        )
                    )

                    # Create answer options
                    answers = q_data.get('answers', [])
                    correct_index = q_data.get('correct')

                    if not answers:
                        self.stdout.write(
                            self.style.WARNING(
                                f'    No answers provided for question'
                            )
                        )
                        continue

                    for idx, answer_text in enumerate(answers):
                        is_correct = (idx == correct_index)
                        
                        AnswerOption.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=is_correct,
                            order=idx + 1,
                        )
                        stats['answers_created'] += 1

                    self.stdout.write(
                        f'    Created {len(answers)} answers '
                        f'(correct: {answers[correct_index] if correct_index is not None else "None"})'
                    )

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Import completed!'))
        self.stdout.write('='*60)
        self.stdout.write(f'State: {state_name}')
        self.stdout.write(f'Tests created: {stats["tests_created"]}')
        self.stdout.write(f'Tests updated (state added): {stats["tests_updated"]}')
        self.stdout.write(f'Questions created: {stats["questions_created"]}')
        self.stdout.write(f'Questions skipped (duplicates): {stats["questions_skipped"]}')
        self.stdout.write(f'Answers created: {stats["answers_created"]}')
        self.stdout.write('='*60)
