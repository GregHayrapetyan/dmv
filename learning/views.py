from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
from .models import (
    Lesson, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson, LessonCategory
)
from .serializers import (
    LessonListSerializer, LessonDetailSerializer,
    TestListSerializer, TestDetailSerializer,
    TestSubmissionSerializer, TestResultSerializer, QuestionDetailSerializer,
    LessonProgressSerializer, TestAttemptSerializer, TestAttemptListSerializer,
    TestAttemptListWithStatsSerializer, FavoriteLessonSerializer, TestStatisticsSerializer,
    TestStatisticsWithAggregatesSerializer, LessonCategoryListSerializer
)
from .permissions import HasActiveSubscriptionOrDemo
from accounts.models import Subscription
import logging

logger = logging.getLogger(__name__)


class LessonListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all lessons grouped by category.
    
    Returns lessons organized by their categories with:
    - Category ID and name
    - Lessons within each category (id, image, name, duration, order)
    """
    serializer_class = LessonCategoryListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    
    @extend_schema(
        summary="List lessons grouped by category",
        description="Retrieve all lessons organized by their categories.",
        responses={
            200: LessonCategoryListSerializer(many=True),
        },
        tags=["Lessons"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return LessonCategory.objects.all().prefetch_related('lessons').order_by('name')


class LessonDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get details of a specific lesson.
    
    Returns full lesson content including text, video URL, and metadata.
    Accessed by lesson ID. Requires active subscription.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    @extend_schema(
        summary="Get lesson detail",
        description="Retrieve full details of a specific lesson by its ID. Requires active subscription.",
        responses={
            200: LessonDetailSerializer,
            403: OpenApiResponse(description="Active subscription required"),
            404: OpenApiResponse(description="Lesson not found"),
        },
        tags=["Lessons"],
    )
    def get(self, request, *args, **kwargs):
        # Check if user has active subscription
        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.has_access():
                return APIResponse.error(
                    message="Active subscription required to access lessons",
                    error_code=ErrorCodes.FORBIDDEN,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="Active subscription required to access lessons",
                error_code=ErrorCodes.FORBIDDEN,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return super().get(request, *args, **kwargs)


class TestListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all tests, optionally filtered by category or demo status.
    
    Returns a list of tests with metadata including passing percentage,
    max attempts, and question count.
    """
    serializer_class = TestListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    
    @extend_schema(
        summary="List tests",
        description="Retrieve all tests. Can filter by demo status.",
        parameters=[
            OpenApiParameter(
                name='demo',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Filter by demo status (true/false)',
                required=False,
            ),
        ],
        responses={
            200: TestListSerializer(many=True),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        from django.db.models import Count
        queryset = Test.objects.all()
        
        # Filter by demo status
        is_demo = self.request.query_params.get('demo', None)
        if is_demo is not None:
            queryset = queryset.filter(is_demo=is_demo.lower() == 'true')
        
        # Filter by user's profile state if authenticated
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                if profile.state:
                    # Show tests for user's state OR tests with no states assigned (available for all)
                    # Annotate with state count to identify tests with no states
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        models.Q(states=profile.state) | models.Q(state_count=0)
                    ).distinct()
            except Exception as e:
                pass  # Profile doesn't exist, show all
        
        return queryset.order_by('id')


class TestDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get a test with all its questions.
    
    Returns complete test details including all questions and answer options.
    Used when a user starts taking a test. Correct answers are not revealed.
    Demo tests are free, premium tests require subscription.
    """
    queryset = Test.objects.all().prefetch_related(
        'questions__answer_options'
    )
    serializer_class = TestDetailSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get test detail",
        description="Retrieve full test details with all questions and answer options. Demo tests are free, premium tests require subscription.",
        responses={
            200: TestDetailSerializer,
            403: OpenApiResponse(description="Active subscription required for premium tests"),
            404: OpenApiResponse(description="Test not found"),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        test = self.get_object()
        
        # Check if test is demo or user has subscription
        if not test.is_demo:
            if not request.user.is_authenticated:
                return APIResponse.error(
                    message="Authentication required for premium tests",
                    error_code=ErrorCodes.UNAUTHORIZED,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            try:
                subscription = Subscription.objects.get(user=request.user)
                if not subscription.has_access():
                    return APIResponse.error(
                        message="Active subscription required to access this test",
                        error_code=ErrorCodes.FORBIDDEN,
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except Subscription.DoesNotExist:
                return APIResponse.error(
                    message="Active subscription required to access this test",
                    error_code=ErrorCodes.FORBIDDEN,
                    status_code=status.HTTP_403_FORBIDDEN
                )

        return super().get(request, *args, **kwargs)



class TestSubmitView(APIView):
    """
    Submit answers for a test and get results.
    
    Accepts a dictionary of answers (question_id: answer_option_id),
    calculates the score, and returns detailed results including correct answers.
    Enforces max attempts limit if configured.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Submit test answers",
        description="Submit answers for a test. Returns score, percentage, pass/fail status, and correct answers. Requires authentication.",
        request=TestSubmissionSerializer,
        examples=[
            OpenApiExample(
                "Submit Test Answers",
                value={
                    "answers": {
                        "1": 2,
                        "2": 5,
                        "3": 8
                    },
                    "time_taken_seconds": 450
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Test submitted successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "attempt_id": 1,
                            "correct_answers": 8,
                            "incorrect_answers": 2,
                            "questions_count": 10,
                            "percentage": 80.0,
                            "passed": True,
                            "questions": [
                                {
                                    "id": 1,
                                    "text": "What does a red octagon sign mean?",
                                    "answer_options": [
                                        {"id": 1, "text": "Stop", "is_correct": True, "explanation": "Red octagon always means stop"},
                                        {"id": 2, "text": "Yield", "is_correct": False, "explanation": ""}
                                    ]
                                }
                            ],
                            "user_answers": {"1": 1, "2": 5}
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Max attempts exceeded or validation error"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Test not found"),
        },
        tags=["Tests"],
    )
    def post(self, request, pk):
        test = get_object_or_404(
            Test.objects.prefetch_related('questions__answer_options'),
            pk=pk
        )
        
        # Check if test is demo or user has subscription
        if not test.is_demo:
            try:
                subscription = Subscription.objects.get(user=request.user)
                if not subscription.has_access():
                    return APIResponse.error(
                        message="Active subscription required to submit this test",
                        error_code=ErrorCodes.FORBIDDEN,
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except Subscription.DoesNotExist:
                return APIResponse.error(
                    message="Active subscription required to submit this test",
                    error_code=ErrorCodes.FORBIDDEN,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        # Check max attempts if configured
        if test.max_attempts:
            attempt_count = TestAttempt.objects.filter(user=request.user, test=test).count()
            if attempt_count >= test.max_attempts:
                return APIResponse.error(
                    message=f'Maximum attempts ({test.max_attempts}) reached for this test',
                    error_code=ErrorCodes.MAX_ATTEMPTS_EXCEEDED,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = TestSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid test submission",
                details=serializer.errors
            )
        
        answers = serializer.validated_data['answers']
        time_taken = request.data.get('time_taken_seconds', None)
        
        # Calculate results
        correct_answers = 0
        incorrect_answers = 0
        answer_records = []
        
        questions = test.questions.all()
        questions_count = questions.count()
        
        for question in questions:
            user_answer_id = answers.get(str(question.id))
            
            selected_option = None
            is_correct = False
            
            if user_answer_id:
                try:
                    selected_option = question.answer_options.get(id=user_answer_id)
                    is_correct = selected_option.is_correct
                    if is_correct:
                        correct_answers += 1
                    else:
                        incorrect_answers += 1
                except AnswerOption.DoesNotExist:
                    logger.warning(f"Invalid answer option {user_answer_id} for question {question.id}")
                    incorrect_answers += 1
            else:
                incorrect_answers += 1
            
            answer_records.append({
                'question': question,
                'selected_option': selected_option,
                'is_correct': is_correct
            })
        
        percentage = Decimal(correct_answers / questions_count * 100) if questions_count > 0 else Decimal(0)
        passed = percentage >= test.passing_percentage
        
        # Create test attempt record
        test_attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            questions_count=questions_count,
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
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'questions_count': questions_count,
            'percentage': float(percentage),
            'passed': passed,
            'questions': question_serializer.data,
            'user_answers': answers
        }
        
        logger.info(f"Test {test.id} submitted by {request.user.email}. Correct: {correct_answers}/{questions_count} ({percentage:.2f}%)")
        
        return APIResponse.success(
            data=result_data,
            message="Test submitted successfully"
        )


class LessonProgressView(APIView):
    """
    Mark a lesson as started or completed.
    
    Creates or updates lesson progress for the authenticated user.
    Used to track which lessons a user has started or completed.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Update lesson progress",
        description="Mark a lesson as started or completed. Creates progress record if it doesn't exist.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "completed": {"type": "boolean", "description": "Whether the lesson is completed"}
                },
                "example": {"completed": True}
            }
        },
        responses={
            200: LessonProgressSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Lesson not found"),
        },
        tags=["Progress"],
    )
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
        return APIResponse.success(
            data=serializer.data,
            message="Lesson progress updated successfully"
        )


class UserLessonProgressListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all lesson progress for the authenticated user.
    
    Returns all lessons the user has started or completed,
    including completion status and timestamps.
    """
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    @extend_schema(
        summary="Get my lesson progress",
        description="Retrieve all lesson progress records for the authenticated user.",
        responses={
            200: LessonProgressSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Progress"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return LessonProgress.objects.filter(user=self.request.user).select_related('lesson')


class UserTestAttemptsListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all test attempts for the authenticated user.
    
    Returns a history of all test attempts with scores and pass/fail status.
    Can be filtered by specific test or pass/fail status.
    """
    serializer_class = TestAttemptListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    @extend_schema(
        summary="Get my test attempts",
        description="Retrieve all test attempts for the authenticated user with aggregated statistics. Can filter by test ID or pass/fail status.",
        parameters=[
            OpenApiParameter(
                name='test',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Filter by specific test ID',
                required=False,
            ),
            OpenApiParameter(
                name='passed',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Filter by pass/fail status (true/false)',
                required=False,
            ),
        ],
        responses={
            200: TestAttemptListWithStatsSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Progress"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = TestAttempt.objects.filter(user=self.request.user).select_related('test')
        
        # Optional filter by test
        test_id = self.request.query_params.get('test', None)
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        
        # Optional filter by passed status
        passed = self.request.query_params.get('passed', None)
        if passed is not None:
            queryset = queryset.filter(passed=passed.lower() == 'true')
        
        return queryset.order_by('-started_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate aggregated statistics across all attempts
        aggregates = queryset.aggregate(
            total_correct_answers=models.Sum('correct_answers'),
            total_incorrect_answers=models.Sum('incorrect_answers'),
            total_questions=models.Sum('questions_count')
        )
        
        total_correct = aggregates['total_correct_answers'] or 0
        total_incorrect = aggregates['total_incorrect_answers'] or 0
        total_questions = aggregates['total_questions'] or 0
        total_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        response_data = {
            'attempts': serializer.data,
            'total_correct_answers': total_correct,
            'total_incorrect_answers': total_incorrect,
            'total_questions': total_questions,
            'total_percentage': round(total_percentage, 2)
        }
        
        return Response(response_data)


class TestAttemptDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get detailed results of a specific test attempt.
    
    Returns complete details of a past test attempt including all questions,
    user's answers, and whether each answer was correct.
    Users can only view their own attempts.
    """
    serializer_class = TestAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get test attempt details",
        description="Retrieve detailed results of a specific test attempt. Includes all answers and correctness. Users can only view their own attempts.",
        responses={
            200: TestAttemptSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Attempt not found or doesn't belong to user"),
        },
        tags=["Progress"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        # Users can only view their own attempts
        return TestAttempt.objects.filter(user=self.request.user).prefetch_related(
            'answers__question',
            'answers__selected_option'
        ).select_related('test')


class AddFavoriteLessonView(APIView):
    """
    Add a lesson to user's favorites.
    
    Creates a favorite record for the authenticated user and specified lesson.
    If already favorited, returns the existing record.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    @extend_schema(
        summary="Add lesson to favorites",
        description="Add a lesson to the authenticated user's favorites. Returns existing record if already favorited.",
        responses={
            201: FavoriteLessonSerializer,
            200: FavoriteLessonSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Lesson not found"),
        },
        tags=["Favorites"],
    )
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        
        favorite, created = FavoriteLesson.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        serializer = FavoriteLessonSerializer(favorite)
        
        if created:
            logger.info(f"User {request.user.email} added lesson {lesson.title} to favorites")
            return APIResponse.success(
                data=serializer.data,
                message="Lesson added to favorites",
                status_code=status.HTTP_201_CREATED
            )
        else:
            return APIResponse.success(
                data=serializer.data,
                message="Lesson already in favorites"
            )


class RemoveFavoriteLessonView(APIView):
    """
    Remove a lesson from user's favorites.
    
    Deletes the favorite record for the authenticated user and specified lesson.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Remove lesson from favorites",
        description="Remove a lesson from the authenticated user's favorites.",
        responses={
            200: OpenApiResponse(description="Lesson removed from favorites"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Favorite not found"),
        },
        tags=["Favorites"],
    )
    def delete(self, request, lesson_id):
        favorite = get_object_or_404(
            FavoriteLesson,
            user=request.user,
            lesson_id=lesson_id
        )
        
        lesson_title = favorite.lesson.title
        favorite.delete()
        
        logger.info(f"User {request.user.email} removed lesson {lesson_title} from favorites")
        
        return APIResponse.success(
            message="Lesson removed from favorites"
        )


class FavoriteLessonsListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all favorite lessons for the authenticated user.
    
    Returns all lessons the user has marked as favorite,
    including lesson details and when it was favorited.
    """
    serializer_class = FavoriteLessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    @extend_schema(
        summary="Get my favorite lessons",
        description="Retrieve all favorite lessons for the authenticated user.",
        responses={
            200: FavoriteLessonSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Favorites"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return FavoriteLesson.objects.filter(user=self.request.user).select_related(
            'lesson'
        )


class TestStatisticsView(StandardizedResponseMixin, generics.ListAPIView):
    """
    Get statistics for all tests showing user's best performance.
    
    Returns a list of all tests with:
    - Test image, title
    - Number of questions
    - User's best percentage score
    - User's best score and total points
    
    Also includes aggregate statistics across all test attempts:
    - Total questions answered
    - Total correct/incorrect answers
    - Overall correct/incorrect percentages
    
    Requires authentication to show personal statistics.
    """
    serializer_class = TestStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    @extend_schema(
        summary="Get test statistics",
        description="Retrieve statistics for all tests including user's best performance and aggregate statistics across all attempts.",
        responses={
            200: TestStatisticsWithAggregatesSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate aggregate statistics across all test attempts for the user
        aggregates = TestAttempt.objects.filter(user=request.user).aggregate(
            total_correct=models.Sum('correct_answers'),
            total_incorrect=models.Sum('incorrect_answers'),
            total_questions=models.Sum('questions_count')
        )
        
        total_correct = aggregates['total_correct'] or 0
        total_incorrect = aggregates['total_incorrect'] or 0
        total_questions = aggregates['total_questions'] or 0
        
        # Calculate percentages
        correct_percentage = round((total_correct / total_questions * 100), 2) if total_questions > 0 else 0
        incorrect_percentage = round((total_incorrect / total_questions * 100), 2) if total_questions > 0 else 0
        
        response_data = {
            'tests': serializer.data,
            'total_questions_answered': total_questions,
            'total_correct_answers': total_correct,
            'total_incorrect_answers': total_incorrect,
            'correct_percentage': correct_percentage,
            'incorrect_percentage': incorrect_percentage
        }
        
        return Response(response_data)
    
    def get_queryset(self):
        from django.db.models import Count
        queryset = Test.objects.all().prefetch_related('questions')
        
        # Filter by user's profile state if authenticated
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                if profile.state:
                    # Show tests for user's state OR tests with no states assigned (available for all)
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        models.Q(states=profile.state) | models.Q(state_count=0)
                    ).distinct()
            except Exception as e:
                pass  # Profile doesn't exist, show all
        
        return queryset.order_by('id')
