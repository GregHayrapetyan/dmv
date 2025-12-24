"""
Migration script to copy existing Test data to CMSTest model.
This allows inline editing of questions and answers in Wagtail CMS.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmv.settings')
django.setup()

from learning.models import Test, Question, AnswerOption
from cms.models import CMSTest, CMSQuestion, CMSAnswer


def migrate_tests():
    """Migrate all tests from learning.Test to cms.CMSTest."""
    
    print("Starting migration of tests to CMS...")
    
    # Get all existing tests
    old_tests = Test.objects.all()
    total_tests = old_tests.count()
    
    print(f"Found {total_tests} tests to migrate")
    
    migrated_count = 0
    
    for old_test in old_tests:
        print(f"\nMigrating test: {old_test.title}")
        
        # Check if already migrated
        if CMSTest.objects.filter(title=old_test.title).exists():
            print(f"  ⚠️  Test '{old_test.title}' already exists in CMS, skipping...")
            continue
        
        # Create new CMSTest
        new_test = CMSTest.objects.create(
            title=old_test.title,
            description=old_test.description,
            # Note: image field is different (ForeignKey to wagtailimages.Image vs ImageField)
            # We'll skip image migration for now
            passing_percentage=old_test.passing_percentage,
            time_limit_seconds=old_test.time_limit_seconds,
            max_attempts=old_test.max_attempts,
            shuffle_questions=old_test.shuffle_questions,
            shuffle_answers=old_test.shuffle_answers,
            created_at=old_test.created_at,
            updated_at=old_test.updated_at,
        )
        
        print(f"  ✓ Created CMSTest: {new_test.title}")
        
        # Migrate questions
        old_questions = old_test.questions.all()
        print(f"  Migrating {old_questions.count()} questions...")
        
        for old_question in old_questions:
            new_question = CMSQuestion.objects.create(
                test=new_test,
                text=old_question.text,
                # Note: image field is different, skipping for now
                question_type=old_question.question_type,
                sort_order=old_question.order,
            )
            
            print(f"    ✓ Created question: {old_question.text[:50]}...")
            
            # Migrate answer options
            old_answers = old_question.answer_options.all()
            print(f"      Migrating {old_answers.count()} answers...")
            
            for old_answer in old_answers:
                new_answer = CMSAnswer.objects.create(
                    question=new_question,
                    text=old_answer.text,
                    is_correct=old_answer.is_correct,
                    explanation=old_answer.explanation,
                    sort_order=old_answer.order,
                )
                
                print(f"        ✓ Created answer: {old_answer.text[:40]}...")
        
        migrated_count += 1
        print(f"  ✅ Test '{old_test.title}' migrated successfully!")
    
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"Migrated {migrated_count} tests out of {total_tests} total")
    print(f"{'='*60}")


if __name__ == '__main__':
    migrate_tests()
