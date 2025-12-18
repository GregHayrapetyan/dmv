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
        fields = ('id', 'text', 'image', 'question_type', 'order', 'answer_options')


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    answer_options = AnswerOptionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'question_type', 'order', 'answer_options')


class TestListSerializer(serializers.ModelSerializer):
    """Serializer for listing tests"""
    lesson_title = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    best_percentage = serializers.SerializerMethodField()
    best_correct_answers = serializers.SerializerMethodField()
    best_incorrect_answers = serializers.SerializerMethodField()
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'lesson_id', 'lesson_title', 'is_demo', 'time_limit_seconds', 'question_count',
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


class TestDetailSerializer(serializers.ModelSerializer):
    """Serializer for taking a test"""
    questions = QuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()
    state_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'image', 'description', 'lesson_id', 'lesson_title', 'time_limit_seconds', 
                  'is_demo', 'questions', 'passing_percentage', 'shuffle_questions', 'shuffle_answers', 'state_names')
    
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


