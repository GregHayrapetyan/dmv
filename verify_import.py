#!/usr/bin/env python
"""Verify the imported questions data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmv.settings')
django.setup()

from learning.models import Test, Question, AnswerOption
from onboarding.models import State

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

# Overall stats
print(f"\n📊 Overall Statistics:")
print(f"  Tests: {Test.objects.count()}")
print(f"  Questions: {Question.objects.count()}")
print(f"  Answers: {AnswerOption.objects.count()}")
print(f"  States: {State.objects.count()}")

# Sample test
print(f"\n📝 Sample Test: Lane Markings")
test = Test.objects.filter(title='Lane Markings').first()
if test:
    print(f"  Title: {test.title}")
    print(f"  States: {', '.join([s.name for s in test.states.all()])}")
    print(f"  Total Questions: {test.questions.count()}")
    print(f"  Passing %: {test.passing_percentage}%")
    print(f"  Shuffle Questions: {test.shuffle_questions}")
    print(f"  Shuffle Answers: {test.shuffle_answers}")
    
    # Sample question
    q = test.questions.first()
    if q:
        print(f"\n📋 Sample Question:")
        print(f"  Text: {q.text}")
        print(f"  Order: {q.order}")
        print(f"  Points: {q.points}")
        print(f"  Answers:")
        for a in q.answer_options.all():
            marker = "✓" if a.is_correct else " "
            print(f"    [{marker}] {a.text}")

# List all tests
print(f"\n📚 All Tests Created:")
for test in Test.objects.all().order_by('title'):
    states = ', '.join([s.name for s in test.states.all()])
    q_count = test.questions.count()
    print(f"  • {test.title} ({q_count} questions) - States: {states}")

print("\n" + "=" * 60)
print("✅ Verification Complete!")
print("=" * 60)
