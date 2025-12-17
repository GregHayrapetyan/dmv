from rest_framework import serializers
from django.db.models import Avg, Count
from .models import (
    Lesson, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson
)


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for listing lessons (without full content)"""
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'lesson_type', 'order', 'duration_minutes', 'is_published', 'state_names')
    
    def get_state_names(self, obj):
        """Return list of state names this lesson is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class LessonDetailSerializer(serializers.ModelSerializer):
    """Serializer for lesson detail view (with full content)"""
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'lesson_type', 'content', 'video_url', 'order', 'duration_minutes', 'created_at', 'state_names')
    
    def get_state_names(self, obj):
        """Return list of state names this lesson is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ('id', 'text', 'is_correct', 'explanation', 'order')


class AnswerOptionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    class Meta:
        model = AnswerOption
        fields = ('id', 'text', 'is_correct', 'explanation', 'order')


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'question_type', 'order', 'points', 'answer_options')


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    answer_options = AnswerOptionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'question_type', 'order', 'points', 'answer_options')


class TestListSerializer(serializers.ModelSerializer):
    """Serializer for listing tests"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    question_count = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()
    best_total_points = serializers.SerializerMethodField()
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'lesson', 'lesson_title', 'is_demo', 'time_limit_seconds', 'question_count',
                  'passing_percentage', 'max_attempts', 'best_percentage', 'best_score', 'best_total_points', 'state_names')
    
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
    
    def get_best_score(self, obj):
        """
        Get the score from the best attempt for the current user for this test.
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
            return best_attempt.score
        return None
    
    def get_best_total_points(self, obj):
        """
        Get the total points from the best attempt for the current user for this test.
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
            return best_attempt.total_points
        return None
    
    def get_state_names(self, obj):
        """Return list of state names this test is available for. Empty list means available for all states."""
        return [state.name for state in obj.states.all()]


class TestDetailSerializer(serializers.ModelSerializer):
    """Serializer for taking a test"""
    questions = QuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'description', 'lesson', 'lesson_title', 'time_limit_seconds', 
                  'is_demo', 'questions', 'passing_percentage', 'shuffle_questions', 'shuffle_answers', 'state_names')
    
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
    score = serializers.IntegerField()
    total_points = serializers.IntegerField()
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
        fields = ('id', 'user', 'user_email', 'test', 'test_title', 'score', 'total_points', 
                  'percentage', 'passed', 'time_taken_seconds', 'started_at', 'completed_at', 'answers')
        read_only_fields = ('user', 'score', 'total_points', 'percentage', 'passed', 'started_at', 'completed_at')


class TestAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing test attempts (without detailed answers)"""
    test_title = serializers.CharField(source='test.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = TestAttempt
        fields = ('id', 'user', 'user_email', 'test', 'test_title', 'score', 'total_points', 
                  'percentage', 'passed', 'time_taken_seconds', 'started_at', 'completed_at')
        read_only_fields = ('user', 'score', 'total_points', 'percentage', 'passed', 'started_at', 'completed_at')


class FavoriteLessonSerializer(serializers.ModelSerializer):
    """Serializer for favorite lessons"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_slug = serializers.CharField(source='lesson.slug', read_only=True)
    lesson_type = serializers.CharField(source='lesson.lesson_type', read_only=True)
    duration_minutes = serializers.IntegerField(source='lesson.duration_minutes', read_only=True)
    
    class Meta:
        model = FavoriteLesson
        fields = ('id', 'lesson', 'lesson_title', 'lesson_slug', 'lesson_type', 'duration_minutes', 'created_at')
        read_only_fields = ('created_at',)


class TestStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for test statistics showing user's best performance"""
    question_count = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()
    best_total_points = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'question_count', 'best_percentage', 'best_score', 'best_total_points')
    
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
    
    def get_best_score(self, obj):
        """
        Get the score from the best attempt for the current user for this test.
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
            return best_attempt.score
        return None
    
    def get_best_total_points(self, obj):
        """
        Get the total points from the best attempt for the current user for this test.
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
            return best_attempt.total_points
        return None


