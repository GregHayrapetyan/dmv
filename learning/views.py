from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption
from .serializers import (
    LessonCategorySerializer, LessonListSerializer, LessonDetailSerializer,
    TestCategorySerializer, TestListSerializer, TestDetailSerializer,
    TestSubmissionSerializer, TestResultSerializer, QuestionDetailSerializer
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
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        test = get_object_or_404(
            Test.objects.prefetch_related('questions__answer_options'),
            pk=pk
        )
        
        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        answers = serializer.validated_data['answers']
        
        # Calculate score
        score = 0
        total_points = 0
        results = []
        
        questions = test.questions.all()
        for question in questions:
            total_points += question.points
            user_answer_id = answers.get(str(question.id))
            
            if user_answer_id:
                try:
                    selected_answer = question.answer_options.get(id=user_answer_id)
                    if selected_answer.is_correct:
                        score += question.points
                except AnswerOption.DoesNotExist:
                    logger.warning(f"Invalid answer option {user_answer_id} for question {question.id}")
        
        percentage = (score / total_points * 100) if total_points > 0 else 0
        passed = percentage >= 70  # 70% passing grade
        
        # Prepare detailed results
        question_serializer = QuestionDetailSerializer(questions, many=True)
        
        result_data = {
            'score': score,
            'total_points': total_points,
            'percentage': round(percentage, 2),
            'passed': passed,
            'questions': question_serializer.data,
            'user_answers': answers
        }
        
        logger.info(f"Test {test.id} submitted. Score: {score}/{total_points} ({percentage:.2f}%)")
        
        return Response(result_data, status=status.HTTP_200_OK)
