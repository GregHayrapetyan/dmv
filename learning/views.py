from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
from .models import (
    LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson
)
from .serializers import (
    LessonCategorySerializer, LessonListSerializer, LessonDetailSerializer,
    TestCategorySerializer, TestListSerializer, TestDetailSerializer,
    TestSubmissionSerializer, TestResultSerializer, QuestionDetailSerializer,
    LessonProgressSerializer, TestAttemptSerializer, TestAttemptListSerializer,
    FavoriteLessonSerializer
)
from .permissions import HasActiveSubscriptionOrDemo
from accounts.models import Subscription
import logging

logger = logging.getLogger(__name__)


class LessonCategoryListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all lesson categories.
    
    Returns all available lesson categories for organizing learning content.
    No authentication required.
    """
    queryset = LessonCategory.objects.all().order_by('name')
    serializer_class = LessonCategorySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List lesson categories",
        description="Retrieve all lesson categories. Used for filtering lessons by category.",
        responses={
            200: LessonCategorySerializer(many=True),
        },
        tags=["Lessons"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LessonListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all lessons, optionally filtered by category.
    
    Returns a list of lessons with basic information.
    Can be filtered by category using query parameter.
    """
    serializer_class = LessonListSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="List lessons",
        description="Retrieve all lessons. Optionally filter by category ID.",
        parameters=[
            OpenApiParameter(
                name='category',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Filter lessons by category ID',
                required=False,
            ),
        ],
        responses={
            200: LessonListSerializer(many=True),
        },
        tags=["Lessons"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Lesson.objects.all().select_related('category')
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.order_by('category', 'id')


class LessonDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get details of a specific lesson.
    
    Returns full lesson content including text, video URL, and metadata.
    Accessed by lesson slug. Requires active subscription.
    """
    queryset = Lesson.objects.all().select_related('category')
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    @extend_schema(
        summary="Get lesson detail",
        description="Retrieve full details of a specific lesson by its slug. Requires active subscription.",
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
                    error_code=ErrorCodes.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="Active subscription required to access lessons",
                error_code=ErrorCodes.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return super().get(request, *args, **kwargs)


class TestCategoryListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all test categories.
    
    Returns all available test categories for organizing tests.
    No authentication required.
    """
    queryset = TestCategory.objects.all().select_related('lesson_category').order_by('name')
    serializer_class = TestCategorySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List test categories",
        description="Retrieve all test categories. Used for filtering tests by category.",
        responses={
            200: TestCategorySerializer(many=True),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TestListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all tests, optionally filtered by category or demo status.
    
    Returns a list of tests with metadata including passing percentage,
    max attempts, and question count.
    """
    serializer_class = TestListSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="List tests",
        description="Retrieve all tests. Can filter by category or demo status.",
        parameters=[
            OpenApiParameter(
                name='category',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Filter tests by category ID',
                required=False,
            ),
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


class TestDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get a test with all its questions.
    
    Returns complete test details including all questions and answer options.
    Used when a user starts taking a test. Correct answers are not revealed.
    Demo tests are free, premium tests require subscription.
    """
    queryset = Test.objects.all().prefetch_related(
        'questions__answer_options'
    ).select_related('lesson', 'test_category')
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
                    error_code=ErrorCodes.AUTHENTICATION_REQUIRED,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            try:
                subscription = Subscription.objects.get(user=request.user)
                if not subscription.has_access():
                    return APIResponse.error(
                        message="Active subscription required to access this test",
                        error_code=ErrorCodes.PERMISSION_DENIED,
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except Subscription.DoesNotExist:
                return APIResponse.error(
                    message="Active subscription required to access this test",
                    error_code=ErrorCodes.PERMISSION_DENIED,
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
        responses={
            200: OpenApiResponse(
                description="Test submitted successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "attempt_id": 1,
                            "score": 8,
                            "total_points": 10,
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
                        error_code=ErrorCodes.PERMISSION_DENIED,
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            except Subscription.DoesNotExist:
                return APIResponse.error(
                    message="Active subscription required to submit this test",
                    error_code=ErrorCodes.PERMISSION_DENIED,
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
        return LessonProgress.objects.filter(user=self.request.user).select_related('lesson', 'lesson__category')


class UserTestAttemptsListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all test attempts for the authenticated user.
    
    Returns a history of all test attempts with scores and pass/fail status.
    Can be filtered by specific test or pass/fail status.
    """
    serializer_class = TestAttemptListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Get my test attempts",
        description="Retrieve all test attempts for the authenticated user. Can filter by test ID or pass/fail status.",
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
            200: TestAttemptListSerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Progress"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
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
            'lesson',
            'lesson__category'
        )
