from rest_framework import serializers
from django.db.models import Avg, Count
from .models import (
    Lesson, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson, LessonCategory
)
from dmv.translation import TranslatedSerializerMixin, get_translated_value


class LessonListSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for listing lessons (without full content). Supports translations via ?lang= query parameter."""
    translated_fields = ['title']
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'image', 'order', 'duration_minutes', 'is_published', 'state_names')
    
    def get_state_names(self, obj):
        """Return list of state names this lesson is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class LessonDetailSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for lesson detail view (with full content). Supports translations via ?lang= query parameter."""
    translated_fields = ['title', 'content']
    duration = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    test_id = serializers.IntegerField(source='test.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content', 'video', 'image', 'order', 'duration', 'is_favorite', 'test_id')
    
    def get_duration(self, obj):
        """Convert duration from minutes to seconds"""
        if obj.duration_minutes:
            # Convert minutes to seconds: multiply by 60
            duration_seconds = float(obj.duration_minutes) * 60
            return round(duration_seconds)
        return 0
    
    def get_is_favorite(self, obj):
        """Check if this lesson is in user's favorites"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteLesson.objects.filter(
                user=request.user,
                lesson=obj
            ).exists()
        return False


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ('id', 'text', 'is_correct', 'order')


class AnswerOptionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    class Meta:
        model = AnswerOption
        fields = ('id', 'text', 'is_correct', 'order')


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'question_type', 'explanation', 'order', 'answer_options')


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    answer_options = AnswerOptionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'question_type', 'explanation', 'order', 'answer_options')


class TestListSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for listing tests. Supports translations via ?lang= query parameter."""
    translated_fields = ['title']
    lesson_title = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    best_correct_answers = serializers.SerializerMethodField()
    best_incorrect_answers = serializers.SerializerMethodField()
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'lesson_id', 'lesson_title', 'time_limit_seconds', 'question_count',
                  'passing_percentage', 'max_attempts', 'best_percentage', 'best_correct_answers', 'best_incorrect_answers', 'state_names')
    
    def get_lesson_title(self, obj):
        """Get the title of the lesson this test belongs to."""
        try:
            return obj.lesson.title
        except:
            return None
    
    def get_lesson_id(self, obj):
        """Get the ID of the lesson this test belongs to."""
        try:
            return obj.lesson.id
        except:
            return None
    
    def get_question_count(self, obj):
        return obj.questions.count()
    
    def get_best_percentage(self, obj):
        """
        Get the best percentage score for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return float(best_attempt.percentage)
        return None
    
    def get_best_correct_answers(self, obj):
        """
        Get the correct answers count from the best attempt for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return best_attempt.correct_answers
        return None
    
    def get_best_incorrect_answers(self, obj):
        """
        Get the incorrect answers count from the best attempt for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return best_attempt.incorrect_answers
        return None
    
    def get_state_names(self, obj):
        """Return list of state names this test is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class TestDetailSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for taking a test. Supports translations via ?lang= query parameter."""
    translated_fields = ['title', 'description']
    questions = QuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'description', 'lesson_id', 'lesson_title', 'time_limit_seconds', 
                  'questions', 'passing_percentage', 'shuffle_questions', 'shuffle_answers', 'state_names')
    
    def get_lesson_title(self, obj):
        """Get the title of the lesson this test belongs to."""
        try:
            return obj.lesson.title
        except:
            return None
    
    def get_lesson_id(self, obj):
        """Get the ID of the lesson this test belongs to."""
        try:
            return obj.lesson.id
        except:
            return None
    
    def get_state_names(self, obj):
        """Return list of state names this test is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class TestSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting test answers"""
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dictionary mapping question_id to selected answer_option_id"
    )
    
    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer must be provided")
        return value


class TestResultSerializer(serializers.Serializer):
    """Serializer for test results"""
    correct_answers = serializers.IntegerField()
    incorrect_answers = serializers.IntegerField()
    questions_count = serializers.IntegerField()
    percentage = serializers.FloatField()
    passed = serializers.BooleanField()
    questions = QuestionDetailSerializer(many=True)
    user_answers = serializers.DictField()


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress tracking"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = ('id', 'user', 'lesson', 'lesson_title', 'completed', 'completed_at', 'started_at', 'updated_at')
        read_only_fields = ('user', 'started_at', 'updated_at')


class TestAnswerSerializer(serializers.ModelSerializer):
    """Serializer for individual test answers"""
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_option_text = serializers.CharField(source='selected_option.text', read_only=True)
    
    class Meta:
        model = TestAnswer
        fields = ('id', 'question', 'question_text', 'selected_option', 'selected_option_text', 'is_correct')


class TestAttemptSerializer(serializers.ModelSerializer):
    """Serializer for test attempts"""
    test_title = serializers.CharField(source='test.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    answers = TestAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ('id', 'user', 'user_email', 'test', 'test_title', 'correct_answers', 'incorrect_answers', 'questions_count',
                  'percentage', 'passed', 'time_taken_seconds', 'started_at', 'completed_at', 'answers')
        read_only_fields = ('user', 'correct_answers', 'incorrect_answers', 'questions_count', 'percentage', 'passed', 'started_at', 'completed_at')


class TestAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing test attempts (without detailed answers)"""
    test_title = serializers.CharField(source='test.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ('id', 'user', 'user_email', 'test', 'test_title', 'correct_answers', 'incorrect_answers', 'questions_count',
                  'percentage', 'passed', 'time_taken_seconds', 'started_at', 'completed_at')
        read_only_fields = ('user', 'correct_answers', 'incorrect_answers', 'questions_count', 'percentage', 'passed', 'started_at', 'completed_at')


class TestAttemptListWithStatsSerializer(serializers.Serializer):
    """Serializer for test attempts list with aggregated statistics"""
    attempts = TestAttemptListSerializer(many=True, read_only=True)
    total_correct_answers = serializers.IntegerField(read_only=True, help_text="Total correct answers across all attempts")
    total_incorrect_answers = serializers.IntegerField(read_only=True, help_text="Total incorrect answers across all attempts")
    total_questions = serializers.IntegerField(read_only=True, help_text="Total questions across all attempts")
    total_percentage = serializers.FloatField(read_only=True, help_text="Overall percentage of correct answers")


class FavoriteLessonSerializer(serializers.ModelSerializer):
    """Serializer for favorite lessons"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    duration_minutes = serializers.IntegerField(source='lesson.duration_minutes', read_only=True)
    
    class Meta:
        model = FavoriteLesson
        fields = ('id', 'lesson', 'lesson_title', 'duration_minutes', 'created_at')
        read_only_fields = ('created_at',)


class TestStatisticsSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for test statistics showing user's best performance. Supports translations via ?lang= query parameter."""
    translated_fields = ['title']
    question_count = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    best_correct_answers = serializers.SerializerMethodField()
    best_incorrect_answers = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'question_count', 'best_percentage', 'best_correct_answers', 'best_incorrect_answers')
    
    def get_question_count(self, obj):
        """Return the total number of questions in this test"""
        return obj.questions.count()
    
    def get_best_percentage(self, obj):
        """
        Get the best percentage score for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return float(best_attempt.percentage)
        return None
    
    def get_best_correct_answers(self, obj):
        """
        Get the correct answers count from the best attempt for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return best_attempt.correct_answers
        return None
    
    def get_best_incorrect_answers(self, obj):
        """
        Get the incorrect answers count from the best attempt for the current user for this test.
        Returns None if user is not authenticated or has no attempts.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the best attempt for this test by the current user
        best_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=obj
        ).order_by('-percentage').first()
        
        if best_attempt:
            return best_attempt.incorrect_answers
        return None


class TestStatisticsWithAggregatesSerializer(serializers.Serializer):
    """Serializer for test statistics response with aggregate data across all attempts"""
    tests = TestStatisticsSerializer(many=True, read_only=True)
    total_questions_answered = serializers.IntegerField(read_only=True, help_text="Total questions answered across all test attempts")
    total_correct_answers = serializers.IntegerField(read_only=True, help_text="Total correct answers across all test attempts")
    total_incorrect_answers = serializers.IntegerField(read_only=True, help_text="Total incorrect answers across all test attempts")
    correct_percentage = serializers.FloatField(read_only=True, help_text="Percentage of correct answers across all attempts")
    incorrect_percentage = serializers.FloatField(read_only=True, help_text="Percentage of incorrect answers across all attempts")


class LessonInCategorySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for lessons within a category. Supports translations via ?lang= query parameter."""
    translated_fields = ['title']
    name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    category_id = serializers.IntegerField(source='category.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'image', 'name', 'duration', 'order', 'category_id')
    
    def get_name(self, obj):
        """Return translated title as name."""
        lang = self.get_language()
        return get_translated_value(obj, 'title', lang)
    
    def get_duration(self, obj):
        """Convert duration from minutes to seconds"""
        if obj.duration_minutes:
            # Convert minutes to seconds: multiply by 60
            duration_seconds = float(obj.duration_minutes) * 60
            return round(duration_seconds)
        return 0


class LessonCategoryListSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for listing categories with their lessons. Supports translations via ?lang= query parameter."""
    translated_fields = ['name']
    category = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonCategory
        fields = ('id', 'category', 'lessons')
    
    def get_category(self, obj):
        """Return translated category name."""
        lang = self.get_language()
        return get_translated_value(obj, 'name', lang)
    
    def get_lessons(self, obj):
        """Get all lessons for this category, filtered by state if applicable"""
        from django.db.models import Count, Q
        
        request = self.context.get('request')
        queryset = obj.lessons.filter(is_published=True)
        
        # Filter by user's profile state if authenticated
        if request and request.user.is_authenticated:
            try:
                profile = request.user.profile
                if profile.state:
                    # Show lessons for user's state OR lessons with no states assigned
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        Q(states=profile.state) | Q(state_count=0)
                    ).distinct()
            except Exception:
                pass  # Profile doesn't exist, show all
        
        queryset = queryset.order_by('order', 'id')
        return LessonInCategorySerializer(queryset, many=True, context=self.context).data


class FavoriteLessonCategorySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for listing favorite lessons grouped by category. Supports translations via ?lang= query parameter."""
    translated_fields = ['name']
    category = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonCategory
        fields = ('id', 'category', 'lessons')
    
    def get_category(self, obj):
        """Return translated category name."""
        lang = self.get_language()
        return get_translated_value(obj, 'name', lang)
    
    def get_lessons(self, obj):
        """Get favorite lessons for this category for the authenticated user"""
        from django.db.models import Count, Q
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        
        # Get lesson IDs that are favorited by the user
        favorite_lesson_ids = FavoriteLesson.objects.filter(
            user=request.user
        ).values_list('lesson_id', flat=True)
        
        # Filter lessons in this category that are favorited
        queryset = obj.lessons.filter(
            id__in=favorite_lesson_ids,
            is_published=True
        )
        
        # Filter by user's profile state if applicable
        try:
            profile = request.user.profile
            if profile.state:
                # Show lessons for user's state OR lessons with no states assigned
                queryset = queryset.annotate(state_count=Count('states'))
                queryset = queryset.filter(
                    Q(states=profile.state) | Q(state_count=0)
                ).distinct()
        except Exception:
            pass  # Profile doesn't exist, show all
        
        queryset = queryset.order_by('order', 'id')
        return LessonInCategorySerializer(queryset, many=True, context=self.context).data


class CategorySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for listing categories (id and name only). Supports translations via ?lang= query parameter."""
    translated_fields = ['name']
    
    class Meta:
        model = LessonCategory
        fields = ('id', 'name')


class CategoryDetailSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for category detail with all videos/lessons. Supports translations via ?lang= query parameter."""
    translated_fields = ['name']
    videos = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonCategory
        fields = ('id', 'name', 'videos')
    
    def get_videos(self, obj):
        """Get all lessons (videos) for this category, filtered by state if applicable"""
        from django.db.models import Count, Q
        
        request = self.context.get('request')
        queryset = obj.lessons.filter(is_published=True)
        
        # Filter by user's profile state if authenticated
        if request and request.user.is_authenticated:
            try:
                profile = request.user.profile
                if profile.state:
                    # Show lessons for user's state OR lessons with no states assigned
                    queryset = queryset.annotate(state_count=Count('states'))
                    queryset = queryset.filter(
                        Q(states=profile.state) | Q(state_count=0)
                    ).distinct()
            except Exception:
                pass  # Profile doesn't exist, show all
        
        queryset = queryset.order_by('order', 'id')
        return LessonInCategorySerializer(queryset, many=True, context=self.context).data


# ============================================================================
# DEMO TEST SERIALIZERS (for non-registered users)
# ============================================================================

class DemoTestRequestSerializer(serializers.Serializer):
    """Serializer for demo test generation request"""
    state_id = serializers.IntegerField(required=True, help_text="State ID for filtering questions")
    vehicle_id = serializers.IntegerField(required=True, help_text="Vehicle type ID for filtering questions")


class DemoTestResponseSerializer(serializers.Serializer):
    """Serializer for demo test response with test_id"""
    test_id = serializers.CharField(help_text="Temporary test ID to use with GET /tests/{id}/?is_demo=true")
