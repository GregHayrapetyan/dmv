import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from cms.models import CMSTest, CMSQuestion, CMSAnswer
from learning.models import Lesson, Test


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_questions_view(request):
    """View for importing questions from JSON file into CMS."""
    
    if request.method == "POST":
        json_file = request.FILES.get('json_file')
        
        if not json_file:
            messages.error(request, "Please select a JSON file to upload.")
            return redirect('cms:import_questions')
        
        try:
            # Read and parse JSON
            content = json_file.read().decode('utf-8')
            data = json.loads(content)
            
            # Handle both list and single object formats
            if isinstance(data, list):
                state_objects = data
            else:
                state_objects = [data]
            
            # Statistics
            stats = {
                'tests_created': 0,
                'tests_updated': 0,
                'questions_created': 0,
                'questions_skipped': 0,
                'answers_created': 0,
            }
            
            # Process each state object
            for state_data in state_objects:
                _process_state_data(state_data, stats)
            
            # Success message
            messages.success(
                request,
                f"Import completed! Tests created: {stats['tests_created']}, "
                f"Questions created: {stats['questions_created']}, "
                f"Answers created: {stats['answers_created']}, "
                f"Questions skipped (duplicates): {stats['questions_skipped']}"
            )
            
        except json.JSONDecodeError as e:
            messages.error(request, f"Invalid JSON file: {e}")
        except Exception as e:
            messages.error(request, f"Import error: {str(e)}")
        
        return redirect('cms:import_questions')
    
    # GET request - show the form
    return render(request, 'cms/import_questions.html', {
        'title': 'Import Questions',
    })


def _process_state_data(data, stats):
    """Process a single state's questions and import to CMS."""
    
    questions_data = data.get('questions', [])
    if not questions_data:
        return
    
    # Group questions by category
    questions_by_category = {}
    for q_data in questions_data:
        category = q_data.get('category', 'General')
        if category not in questions_by_category:
            questions_by_category[category] = []
        questions_by_category[category].append(q_data)
    
    # Process each category
    for category, questions in questions_by_category.items():
        with transaction.atomic():
            # Get or create CMSTest for this category
            test_title = category.replace('_', ' ').title()
            test, test_created = CMSTest.objects.get_or_create(
                title=test_title,
                defaults={
                    'description': f'Test for {test_title}',
                    'passing_percentage': 100,
                    'shuffle_questions': True,
                    'shuffle_answers': True,
                }
            )
            
            if test_created:
                stats['tests_created'] += 1
            else:
                stats['tests_updated'] += 1
            
            # Process questions for this test
            for q_data in questions:
                question_text = q_data.get('question')
                if not question_text:
                    continue
                
                # Check if question already exists (by text)
                existing_question = CMSQuestion.objects.filter(
                    test=test,
                    text=question_text
                ).first()
                
                if existing_question:
                    stats['questions_skipped'] += 1
                    continue
                
                # Get the next order number for this test
                max_order = CMSQuestion.objects.filter(test=test).count()
                
                # Get explanation from JSON
                explanation = q_data.get('explanation', '')
                
                # Create question
                question = CMSQuestion.objects.create(
                    test=test,
                    text=question_text,
                    question_type='multiple_choice',
                    explanation=explanation,
                    order=max_order + 1
                )
                stats['questions_created'] += 1
                
                # Create answer options
                answers = q_data.get('answers', [])
                correct_index = q_data.get('correct')
                
                if not answers:
                    continue
                
                for idx, answer_text in enumerate(answers):
                    is_correct = (idx == correct_index)
                    
                    CMSAnswer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=is_correct,
                        order=idx + 1,
                    )
                    stats['answers_created'] += 1


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def reorder_tests_view(request):
    """AJAX view to reorder CMSTest items via drag-and-drop."""
    try:
        data = json.loads(request.body)
        ordered_ids = data.get('ordered_ids', [])
        
        if not ordered_ids:
            return JsonResponse({'status': 'error', 'message': 'No items provided'}, status=400)
        
        with transaction.atomic():
            for index, item_id in enumerate(ordered_ids):
                CMSTest.objects.filter(pk=item_id).update(order=index)
                # Sync order to learning.Test (QuerySet.update bypasses post_save signals)
                cms_test = CMSTest.objects.filter(pk=item_id).values_list('title', flat=True).first()
                if cms_test:
                    Test.objects.filter(title=cms_test).update(order=index)
        
        return JsonResponse({'status': 'ok', 'message': f'Reordered {len(ordered_ids)} tests'})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def reorder_lessons_view(request):
    """AJAX view to reorder Lesson items via drag-and-drop."""
    try:
        data = json.loads(request.body)
        ordered_ids = data.get('ordered_ids', [])
        
        if not ordered_ids:
            return JsonResponse({'status': 'error', 'message': 'No items provided'}, status=400)
        
        with transaction.atomic():
            for index, item_id in enumerate(ordered_ids):
                Lesson.objects.filter(pk=item_id).update(order=index)
        
        return JsonResponse({'status': 'ok', 'message': f'Reordered {len(ordered_ids)} lessons'})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
