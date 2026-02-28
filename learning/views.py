from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from django.core.cache import cache
from decimal import Decimal
import random
import hashlib
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
    TestStatisticsWithAggregatesSerializer, LessonCategoryListSerializer, LessonInCategorySerializer,
    CategorySerializer, CategoryDetailSerializer,
    DemoTestRequestSerializer, DemoTestResponseSerializer, QuestionSerializer
)
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
        description="Retrieve all lessons organized by their categories. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
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
        description="Retrieve full details of a specific lesson by its ID. Requires active subscription. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
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
        description="Retrieve all tests. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
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
        
        # Filter by user's profile state and vehicle if authenticated
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                
                # Filter by state
                if profile.state:
                    # Show tests for user's state OR tests with no states assigned (available for all)
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        models.Q(states=profile.state) | models.Q(state_count=0)
                    ).distinct()
                
                # Filter by vehicle type
                if profile.vehicle:
                    # Show tests for user's vehicle OR tests with no vehicles assigned (available for all)
                    queryset = queryset.annotate(vehicle_count=Count('vehicles'))
                    queryset = queryset.filter(
                        models.Q(vehicles=profile.vehicle) | models.Q(vehicle_count=0)
                    ).distinct()
            except Exception as e:
                pass  # Profile doesn't exist, show all
        
        return queryset.order_by('id')


class TestDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get a test with all its questions.
    
    Returns complete test details including all questions and answer options.
    Used when a user starts taking a test. Correct answers are not revealed.
    Requires active subscription.
    """
    queryset = Test.objects.all().prefetch_related(
        'questions__answer_options'
    )
    serializer_class = TestDetailSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get test detail",
        description="Retrieve full test details with all questions and answer options. Requires active subscription unless is_demo=true. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='is_demo',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Set to true for demo test (returns 15 random questions)',
                required=False,
            ),
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        responses={
            200: TestDetailSerializer,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Active subscription required"),
            404: OpenApiResponse(description="Test not found or demo session expired"),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        is_demo = request.query_params.get('is_demo', '').lower() == 'true'
        test_id = kwargs.get('pk')
        
        if is_demo:
            # Handle demo test request
            # Verify this is a valid demo session
            demo_session = cache.get(f'demo_test_{test_id}')
            if not demo_session:
                return APIResponse.error(
                    message="Demo test session not found or expired. Please generate a new demo test.",
                    error_code=ErrorCodes.NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Get state and vehicle from session
            state_id = demo_session.get('state_id')
            vehicle_id = demo_session.get('vehicle_id')
            
            # Find tests matching the criteria
            from django.db.models import Count, Q
            from onboarding.models import State, Vehicle
            
            try:
                state = State.objects.get(id=state_id)
                vehicle = Vehicle.objects.get(id=vehicle_id)
            except (State.DoesNotExist, Vehicle.DoesNotExist):
                return APIResponse.error(
                    message="Invalid state or vehicle in session",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            tests = Test.objects.annotate(
                state_count=Count('states'),
                vehicle_count=Count('vehicles')
            ).filter(
                Q(states=state) | Q(state_count=0)
            ).filter(
                Q(vehicles=vehicle) | Q(vehicle_count=0)
            ).distinct()
            
            if not tests.exists():
                return APIResponse.error(
                    message="No tests available for the selected state and vehicle",
                    error_code=ErrorCodes.NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Get 15 random questions from matching tests
            all_questions = Question.objects.filter(
                test__in=tests
            ).prefetch_related('answer_options').order_by('?')
            
            if all_questions.count() < 15:
                return APIResponse.error(
                    message=f"Insufficient questions available. Found {all_questions.count()}, need 15",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Select 15 random questions
            selected_questions = list(all_questions[:15])
            random.shuffle(selected_questions)
            
            # Store question IDs in cache for potential future use
            demo_session['question_ids'] = [q.id for q in selected_questions]
            cache.set(f'demo_test_{test_id}', demo_session, timeout=3600)
            
            # Prepare response with demo questions
            question_serializer = QuestionSerializer(selected_questions, many=True)
            
            response_data = {
                'id': test_id,
                'time_limit_seconds': 120,
                'questions': question_serializer.data
            }
            
            logger.info(f"Demo test {test_id} accessed with {len(selected_questions)} questions")
            
            return APIResponse.success(
                data=response_data,
                message="Demo test retrieved successfully"
            )
        
        # Regular test - validate that pk is an integer
        try:
            test_id_int = int(test_id)
            kwargs['pk'] = test_id_int
        except (ValueError, TypeError):
            return APIResponse.error(
                message="Invalid test ID format. For demo tests, use ?is_demo=true parameter.",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Regular test - require authentication and subscription
        if not request.user.is_authenticated:
            return APIResponse.error(
                message="Authentication required",
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
        
        # All tests require subscription
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
    
    Returns a flat list of favorite lessons with:
    - Lesson ID, image, name, duration, order
    """
    serializer_class = LessonInCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    @extend_schema(
        summary="Get my favorite lessons",
        description="Retrieve all favorite lessons for the authenticated user as a flat list.",
        responses={
            200: LessonInCategorySerializer(many=True),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Favorites"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        from django.db.models import Count, Q
        
        # Get lesson IDs that are favorited by the user
        favorite_lesson_ids = FavoriteLesson.objects.filter(
            user=self.request.user
        ).values_list('lesson_id', flat=True)
        
        # Get the lessons
        queryset = Lesson.objects.filter(
            id__in=favorite_lesson_ids,
            is_published=True
        )
        
        # Filter by user's profile state if applicable
        try:
            profile = self.request.user.profile
            if profile.state:
                # Show lessons for user's state OR lessons with no states assigned
                queryset = queryset.annotate(state_count=Count('states'))
                queryset = queryset.filter(
                    Q(states=profile.state) | Q(state_count=0)
                ).distinct()
        except Exception:
            pass  # Profile doesn't exist, show all
        
        return queryset.order_by('order', 'id')


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
        
        # Filter by user's profile state and vehicle if authenticated
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.profile
                
                # Filter by state
                if profile.state:
                    # Show tests for user's state OR tests with no states assigned (available for all)
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        models.Q(states=profile.state) | models.Q(state_count=0)
                    ).distinct()
                
                # Filter by vehicle type
                if profile.vehicle:
                    # Show tests for user's vehicle OR tests with no vehicles assigned (available for all)
                    queryset = queryset.annotate(vehicle_count=Count('vehicles'))
                    queryset = queryset.filter(
                        models.Q(vehicles=profile.vehicle) | models.Q(vehicle_count=0)
                    ).distinct()
            except Exception as e:
                pass  # Profile doesn't exist, show all
        
        return queryset.order_by('id')


class CategoryListView(StandardizedResponseMixin, generics.ListAPIView):
    """
    List all categories with id and name.
    
    Returns a simple list of all lesson categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    queryset = LessonCategory.objects.all().order_by('name')
    
    @extend_schema(
        summary="List all categories",
        description="Retrieve all lesson categories with id and name.",
        responses={
            200: CategorySerializer(many=True),
        },
        tags=["Categories"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CategoryDetailView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get category details with all videos/lessons.
    
    Returns category name and all videos (lessons) within that category.
    """
    serializer_class = CategoryDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = LessonCategory.objects.all()
    lookup_field = 'pk'
    
    @extend_schema(
        summary="Get category detail with videos",
        description="Retrieve category details including name and all videos/lessons in that category.",
        responses={
            200: CategoryDetailSerializer,
            404: OpenApiResponse(description="Category not found"),
        },
        tags=["Categories"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ============================================================================
# DEMO TEST VIEWS (for non-registered users)
# ============================================================================

class DemoTestGenerateView(APIView):
    """
    Generate a demo test for non-registered users.
    
    Creates a temporary test_id that can be used with tests/<id>/?is_demo=true
    to retrieve 15 random questions. Session expires in 1 hour.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Generate demo test",
        description="Generate a temporary demo test ID. Use this ID with GET /tests/{id}/?is_demo=true to retrieve questions.",
        request=DemoTestRequestSerializer,
        responses={
            200: DemoTestResponseSerializer,
        },
        tags=["Demo Tests"],
    )
    def post(self, request):
        serializer = DemoTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid request data",
                details=serializer.errors
            )
        
        state_id = serializer.validated_data['state_id']
        vehicle_id = serializer.validated_data['vehicle_id']
        
        # Validate state and vehicle exist
        from onboarding.models import State, Vehicle
        try:
            state = State.objects.get(id=state_id)
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except (State.DoesNotExist, Vehicle.DoesNotExist):
            return APIResponse.error(
                message="Invalid state or vehicle selection",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique temporary test ID
        session_data = f"demo-{state_id}-{vehicle_id}-{timezone.now().timestamp()}-{random.randint(1000, 9999)}"
        test_id = hashlib.md5(session_data.encode()).hexdigest()
        
        # Store demo session in cache (expires in 1 hour)
        demo_session = {
            'created_at': timezone.now().isoformat(),
            'is_demo': True,
            'state_id': state_id,
            'vehicle_id': vehicle_id
        }
        cache.set(f'demo_test_{test_id}', demo_session, timeout=3600)
        
        response_data = {
            'test_id': test_id
        }
        
        logger.info(f"Demo test generated with ID: {test_id}, State: {state_id}, Vehicle: {vehicle_id}")
        
        return APIResponse.success(
            data=response_data,
            message="Demo test ID generated successfully. Use this ID with GET /tests/{id}/?is_demo=true"
        )


# ============================================================================
# MIXED TEST VIEWS (random questions from all tests)
# ============================================================================

MIXED_TEST_QUESTION_COUNT = 20
MIXED_TEST_PASSING_PERCENTAGE = 80


class MixedTestView(APIView):
    """
    Generate a mixed screening test with random questions from all available tests.
    
    Returns 20 random questions pulled from all tests matching the user's
    state and vehicle profile. Requires authentication and active subscription.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get mixed screening test",
        description="Generate a mixed test with 20 random questions from all available tests. "
                    "Questions are filtered by user's state and vehicle profile. Requires active subscription.",
        parameters=[
            OpenApiParameter(
                name='lang',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Language code for translations (en, ru, hy, hi, es, zh). Defaults to en.',
                required=False,
                enum=['en', 'ru', 'hy', 'hi', 'es', 'zh'],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Mixed test generated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "questions_count": 20,
                            "time_limit_seconds": None,
                            "passing_percentage": 80,
                            "questions": []
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Not enough questions available"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Active subscription required"),
        },
        tags=["Tests"],
    )
    def get(self, request):
        # Check subscription
        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.has_access():
                return APIResponse.error(
                    message="Active subscription required to access mixed test",
                    error_code=ErrorCodes.FORBIDDEN,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="Active subscription required to access mixed test",
                error_code=ErrorCodes.FORBIDDEN,
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Get tests filtered by user's state/vehicle
        from django.db.models import Count, Q
        queryset = Test.objects.all()

        try:
            profile = request.user.profile

            if profile.state:
                queryset = queryset.annotate(state_count=Count('states'))
                queryset = queryset.filter(
                    Q(states=profile.state) | Q(state_count=0)
                ).distinct()

            if profile.vehicle:
                queryset = queryset.annotate(vehicle_count=Count('vehicles'))
                queryset = queryset.filter(
                    Q(vehicles=profile.vehicle) | Q(vehicle_count=0)
                ).distinct()
        except Exception:
            pass

        # Pick random questions from all matching tests
        all_questions = Question.objects.filter(
            test__in=queryset
        ).prefetch_related('answer_options').order_by('?')

        total_available = all_questions.count()
        if total_available < MIXED_TEST_QUESTION_COUNT:
            return APIResponse.error(
                message=f"Not enough questions available ({total_available} found, need {MIXED_TEST_QUESTION_COUNT})",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        selected_questions = list(all_questions[:MIXED_TEST_QUESTION_COUNT])
        random.shuffle(selected_questions)

        serializer = QuestionSerializer(selected_questions, many=True)

        response_data = {
            'questions_count': len(selected_questions),
            'time_limit_seconds': None,
            'passing_percentage': MIXED_TEST_PASSING_PERCENTAGE,
            'questions': serializer.data,
        }

        logger.info(f"Mixed test generated for user {request.user.email} with {len(selected_questions)} questions")

        return APIResponse.success(
            data=response_data,
            message="Mixed test generated successfully"
        )


class MixedTestSubmitView(APIView):
    """
    Submit answers for a mixed screening test.
    
    Accepts a dictionary of answers (question_id: answer_option_id),
    calculates the score across questions from multiple tests,
    and returns detailed results including correct answers.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Submit mixed test answers",
        description="Submit answers for a mixed screening test. Returns score, percentage, pass/fail status, and correct answers.",
        request=TestSubmissionSerializer,
        examples=[
            OpenApiExample(
                "Submit Mixed Test Answers",
                value={
                    "answers": {
                        "1": 2,
                        "2": 5,
                        "3": 8
                    },
                    "time_taken_seconds": 600
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Mixed test submitted successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "attempt_id": 1,
                            "correct_answers": 16,
                            "incorrect_answers": 4,
                            "questions_count": 20,
                            "percentage": 80.0,
                            "passed": True,
                            "questions": [],
                            "user_answers": {"1": 2, "2": 5}
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Active subscription required"),
        },
        tags=["Tests"],
    )
    def post(self, request):
        # Check subscription
        try:
            subscription = Subscription.objects.get(user=request.user)
            if not subscription.has_access():
                return APIResponse.error(
                    message="Active subscription required to submit mixed test",
                    error_code=ErrorCodes.FORBIDDEN,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except Subscription.DoesNotExist:
            return APIResponse.error(
                message="Active subscription required to submit mixed test",
                error_code=ErrorCodes.FORBIDDEN,
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = TestSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid test submission",
                details=serializer.errors
            )

        answers = serializer.validated_data['answers']
        time_taken = request.data.get('time_taken_seconds', None)

        # Resolve questions by IDs from the answers
        question_ids = [int(qid) for qid in answers.keys()]
        questions = Question.objects.filter(
            id__in=question_ids
        ).prefetch_related('answer_options')

        # Calculate results
        correct_answers = 0
        incorrect_answers = 0
        answer_records = []

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

        questions_count = len(question_ids)
        percentage = Decimal(correct_answers / questions_count * 100) if questions_count > 0 else Decimal(0)
        passed = percentage >= MIXED_TEST_PASSING_PERCENTAGE

        # Create test attempt record (test=None, is_mixed=True)
        test_attempt = TestAttempt.objects.create(
            user=request.user,
            test=None,
            is_mixed=True,
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

        logger.info(f"Mixed test submitted by {request.user.email}. Correct: {correct_answers}/{questions_count} ({percentage:.2f}%)")

        return APIResponse.success(
            data=result_data,
            message="Mixed test submitted successfully"
        )
