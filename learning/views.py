from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from .models import (
    LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer
)
from .serializers import (
    LessonCategorySerializer, LessonListSerializer, LessonDetailSerializer,
    TestCategorySerializer, TestListSerializer, TestDetailSerializer,
    TestSubmissionSerializer, TestResultSerializer, QuestionDetailSerializer,
    LessonProgressSerializer, TestAttemptSerializer, TestAttemptListSerializer
)
import logging

logger = logging.getLogger(__name__)


class LessonCategoryListView(generics.ListAPIView):
    """List all lesson categories"""
    queryset = LessonCategory.objects.all().order_by('name')
    serializer_class = LessonCategorySerializer
    permission_classes = [permissions.AllowAny]


class LessonListView(generics.ListAPIView):
    """List all lessons, optionally filtered by category"""
    serializer_class = LessonListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Lesson.objects.all().select_related('category')
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.order_by('category', 'id')


class LessonDetailView(generics.RetrieveAPIView):
    """Get details of a specific lesson"""
    queryset = Lesson.objects.all().select_related('category')
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class TestCategoryListView(generics.ListAPIView):
    """List all test categories"""
    queryset = TestCategory.objects.all().select_related('lesson_category').order_by('name')
    serializer_class = TestCategorySerializer
    permission_classes = [permissions.AllowAny]


class TestListView(generics.ListAPIView):
    """List all tests, optionally filtered by category or demo status"""
    serializer_class = TestListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Test.objects.all().select_related('lesson', 'test_category')
        
        # Filter by test category
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(test_category_id=category_id)
        
        # Filter by demo status
        is_demo = self.request.query_params.get('demo', None)
        if is_demo is not None:
            queryset = queryset.filter(is_demo=is_demo.lower() == 'true')
        
        return queryset.order_by('test_category', 'id')


class TestDetailView(generics.RetrieveAPIView):
    """Get a test with all its questions (for taking the test)"""
    queryset = Test.objects.all().prefetch_related(
        'questions__answer_options'
    ).select_related('lesson', 'test_category')
    serializer_class = TestDetailSerializer
    permission_classes = [permissions.AllowAny]


class TestSubmitView(APIView):
    """Submit answers for a test and get results"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        test = get_object_or_404(
            Test.objects.prefetch_related('questions__answer_options'),
            pk=pk
        )
        
        # Check max attempts if configured
        if test.max_attempts:
            attempt_count = TestAttempt.objects.filter(user=request.user, test=test).count()
            if attempt_count >= test.max_attempts:
                return Response(
                    {'error': f'Maximum attempts ({test.max_attempts}) reached for this test'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        answers = serializer.validated_data['answers']
        time_taken = request.data.get('time_taken_seconds', None)
        
        # Calculate score
        score = 0
        total_points = 0
        answer_records = []
        
        questions = test.questions.all()
        for question in questions:
            total_points += question.points
            user_answer_id = answers.get(str(question.id))
            
            selected_option = None
            is_correct = False
            
            if user_answer_id:
                try:
                    selected_option = question.answer_options.get(id=user_answer_id)
                    is_correct = selected_option.is_correct
                    if is_correct:
                        score += question.points
                except AnswerOption.DoesNotExist:
                    logger.warning(f"Invalid answer option {user_answer_id} for question {question.id}")
            
            answer_records.append({
                'question': question,
                'selected_option': selected_option,
                'is_correct': is_correct
            })
        
        percentage = Decimal(score / total_points * 100) if total_points > 0 else Decimal(0)
        passed = percentage >= test.passing_percentage
        
        # Create test attempt record
        test_attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            score=score,
            total_points=total_points,
            percentage=percentage,
            passed=passed,
            time_taken_seconds=time_taken,
            completed_at=timezone.now()
        )
        
        # Create answer records
        for answer_data in answer_records:
            TestAnswer.objects.create(
                attempt=test_attempt,
                question=answer_data['question'],
                selected_option=answer_data['selected_option'],
                is_correct=answer_data['is_correct']
            )
        
        # Prepare detailed results
        question_serializer = QuestionDetailSerializer(questions, many=True)
        
        result_data = {
            'attempt_id': test_attempt.id,
            'score': score,
            'total_points': total_points,
            'percentage': float(percentage),
            'passed': passed,
            'questions': question_serializer.data,
            'user_answers': answers
        }
        
        logger.info(f"Test {test.id} submitted by {request.user.email}. Score: {score}/{total_points} ({percentage:.2f}%)")
        
        return Response(result_data, status=status.HTTP_200_OK)


class LessonProgressView(APIView):
    """Mark a lesson as started or completed"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        completed = request.data.get('completed', False)
        
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'completed': completed}
        )
        
        if not created:
            progress.completed = completed
            if completed and not progress.completed_at:
                progress.completed_at = timezone.now()
            progress.save()
        elif completed:
            progress.completed_at = timezone.now()
            progress.save()
        
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLessonProgressListView(generics.ListAPIView):
    """List all lesson progress for the authenticated user"""
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user).select_related('lesson', 'lesson__category')


class UserTestAttemptsListView(generics.ListAPIView):
    """List all test attempts for the authenticated user"""
    serializer_class = TestAttemptListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = TestAttempt.objects.filter(user=self.request.user).select_related('test', 'test__lesson')
        
        # Optional filter by test
        test_id = self.request.query_params.get('test', None)
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        
        # Optional filter by passed status
        passed = self.request.query_params.get('passed', None)
        if passed is not None:
            queryset = queryset.filter(passed=passed.lower() == 'true')
        
        return queryset.order_by('-started_at')


class TestAttemptDetailView(generics.RetrieveAPIView):
    """Get detailed results of a specific test attempt"""
    serializer_class = TestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only view their own attempts
        return TestAttempt.objects.filter(user=self.request.user).prefetch_related(
            'answers__question',
            'answers__selected_option'
        ).select_related('test')
