from rest_framework import serializers
from .models import (
    LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer
)


class LessonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCategory
        fields = ('id', 'name', 'slug', 'description')


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for listing lessons (without full content)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'category', 'category_name', 'lesson_type', 'order', 'duration_minutes', 'is_published')


class LessonDetailSerializer(serializers.ModelSerializer):
    """Serializer for lesson detail view (with full content)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'category', 'category_name', 
                  'lesson_type', 'content', 'video_url', 'order', 'duration_minutes', 'created_at')


class TestCategorySerializer(serializers.ModelSerializer):
    lesson_category_name = serializers.CharField(source='lesson_category.name', read_only=True)
    
    class Meta:
        model = TestCategory
        fields = ('id', 'name', 'slug', 'lesson_category', 'lesson_category_name')


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ('id', 'text', 'order')
        # Don't expose is_correct or explanation in list view


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
    test_category_name = serializers.CharField(source='test_category.name', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'lesson', 'lesson_title', 'test_category', 
                  'test_category_name', 'is_demo', 'time_limit_seconds', 'question_count',
                  'passing_percentage', 'max_attempts')
    
    def get_question_count(self, obj):
        return obj.questions.count()


class TestDetailSerializer(serializers.ModelSerializer):
    """Serializer for taking a test"""
    questions = QuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    test_category_name = serializers.CharField(source='test_category.name', read_only=True)
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'description', 'lesson', 'lesson_title', 
                  'test_category', 'test_category_name', 'time_limit_seconds', 
                  'is_demo', 'questions', 'passing_percentage', 'shuffle_questions', 'shuffle_answers')


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
