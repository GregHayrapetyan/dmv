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
    MixedTestResponseSerializer, QuestionSerializer
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
        description="Retrieve full test details with all questions and answer options. Requires active subscription unless is_mixed=true. Supports translations via ?lang= query parameter.",
        parameters=[
            OpenApiParameter(
                name='is_mixed',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Set to true for mixed test (returns configured random questions per test)',
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
            404: OpenApiResponse(description="Test not found or mixed test session expired"),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        is_mixed = request.query_params.get('is_mixed', '').lower() == 'true'
        test_id = kwargs.get('pk')
        
        if is_mixed:
            # Handle mixed test request
            # Verify this is a valid mixed test session
            mixed_session = cache.get(f'mixed_test_{test_id}')
            if not mixed_session:
                return APIResponse.error(
                    message="Mixed test session not found or expired. Please generate a new mixed test.",
                    error_code=ErrorCodes.NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Require authentication to access mixed test
            if not request.user.is_authenticated:
                return APIResponse.error(
                    message="Authentication required",
                    error_code=ErrorCodes.UNAUTHORIZED,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get state and vehicle from user profile
            from django.db.models import Count, Q
            from onboarding.models import Profile
            
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                return APIResponse.error(
                    message="User profile not found. Please complete onboarding first.",
                    error_code=ErrorCodes.NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            state = profile.state
            vehicle = profile.vehicle
            
            if not state or not vehicle:
                return APIResponse.error(
                    message="Please select a state and vehicle in your profile first.",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Find tests matching the user's state and vehicle that contribute to mixed test
            tests = Test.objects.annotate(
                state_count=Count('states'),
                vehicle_count=Count('vehicles')
            ).filter(
                Q(states=state) | Q(state_count=0)
            ).filter(
                Q(vehicles=vehicle) | Q(vehicle_count=0)
            ).filter(
                mixed_question_count__gt=0
            ).distinct()
            
            if not tests.exists():
                return APIResponse.error(
                    message="No tests configured for the mixed screening test",
                    error_code=ErrorCodes.NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Pull the configured number of random questions from each test
            selected_questions = []
            for test in tests:
                count = test.mixed_question_count
                questions = list(
                    Question.objects.filter(test=test)
                    .prefetch_related('answer_options')
                    .order_by('?')[:count]
                )
                if len(questions) < count:
                    logger.warning(
                        f"Test '{test.title}' (id={test.id}) has {len(questions)} questions "
                        f"but mixed_question_count is {count}"
                    )
                selected_questions.extend(questions)
            
            if not selected_questions:
                return APIResponse.error(
                    message="No questions available for the mixed screening test",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            random.shuffle(selected_questions)
            
            # Store question IDs in cache for potential future use
            mixed_session['question_ids'] = [q.id for q in selected_questions]
            cache.set(f'mixed_test_{test_id}', mixed_session, timeout=3600)
            
            # Prepare response with mixed test questions
            question_serializer = QuestionSerializer(selected_questions, many=True, context={'request': request})
            
            response_data = {
                'id': test_id,
                'time_limit_seconds': 120,
                'questions': question_serializer.data
            }
            
            logger.info(f"Mixed test {test_id} accessed with {len(selected_questions)} questions")
            
            return APIResponse.success(
                data=response_data,
                message="Mixed test retrieved successfully"
            )
        
        # Regular test - validate that pk is an integer
        try:
            test_id_int = int(test_id)
            kwargs['pk'] = test_id_int
        except (ValueError, TypeError):
            return APIResponse.error(
                message="Invalid test ID format. For mixed tests, use ?is_mixed=true parameter.",
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
# DEMO TEST VIEW (for non-registered users)
# ============================================================================

class DemoTestView(StandardizedResponseMixin, generics.RetrieveAPIView):
    """
    Get the demo test with all its questions.
    
    Returns the first test marked as is_demo=True, including all questions 
    and answer options. No authentication required. Correct answers are not revealed.
    """
    serializer_class = TestDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Get demo test",
        description="Retrieve the demo test with all questions and answer options. No authentication required. Supports translations via ?lang= query parameter.",
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
            200: TestDetailSerializer,
            404: OpenApiResponse(description="Demo test not found"),
        },
        tags=["Tests"],
    )
    def get(self, request, *args, **kwargs):
        # Find the first demo test
        demo_test = Test.objects.filter(is_demo=True).prefetch_related(
            'questions__answer_options'
        ).first()
        
        if not demo_test:
            return APIResponse.error(
                message="Demo test not found. Please contact support.",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Use the serializer to format the response
        serializer = self.get_serializer(demo_test)
        
        logger.info(f"Demo test {demo_test.id} accessed")
        
        return APIResponse.success(
            data=serializer.data,
            message="Demo test retrieved successfully"
        )


# ============================================================================
# MIXED TEST VIEWS (for non-registered users)
# ============================================================================

class MixedTestGenerateView(APIView):
    """
    Generate a mixed test for non-registered users.
    
    Creates a temporary test_id that can be used with tests/<id>/?is_mixed=true
    to retrieve 20 random questions. Session expires in 1 hour.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Generate mixed test",
        description="Generate a temporary mixed test ID. Use this ID with GET /tests/{id}/?is_mixed=true to retrieve questions.",
        responses={
            200: MixedTestResponseSerializer,
        },
        tags=["Mixed Tests"],
    )
    def get(self, request):
        # Generate unique temporary test ID
        session_data = f"mixed-{timezone.now().timestamp()}-{random.randint(1000, 9999)}"
        test_id = hashlib.md5(session_data.encode()).hexdigest()
        
        # Store mixed test session in cache (expires in 1 hour)
        mixed_session = {
            'created_at': timezone.now().isoformat(),
            'is_mixed': True,
        }
        cache.set(f'mixed_test_{test_id}', mixed_session, timeout=3600)
        
        response_data = {
            'test_id': test_id
        }
        
        logger.info(f"Mixed test generated with ID: {test_id}")
        
        return APIResponse.success(
            data=response_data,
            message="Mixed test ID generated successfully. Use this ID with GET /tests/{id}/?is_mixed=true"
        )
