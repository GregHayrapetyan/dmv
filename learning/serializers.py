from rest_framework import serializers
from .models import LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption


class LessonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonCategory
        fields = ('id', 'name', 'slug', 'description')


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for listing lessons (without full content)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'category', 'category_name', 'lesson_type')


class LessonDetailSerializer(serializers.ModelSerializer):
    """Serializer for lesson detail view (with full content)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'slug', 'category', 'category_name', 
                  'lesson_type', 'content', 'video_url')


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
        fields = ('id', 'text', 'image', 'order', 'points', 'answer_options')


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used after submission to show correct answers"""
    answer_options = AnswerOptionDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'order', 'points', 'answer_options')


class TestListSerializer(serializers.ModelSerializer):
    """Serializer for listing tests"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    test_category_name = serializers.CharField(source='test_category.name', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ('id', 'title', 'lesson', 'lesson_title', 'test_category', 
                  'test_category_name', 'is_demo', 'time_limit_seconds', 'question_count')
    
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
                  'is_demo', 'questions')


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
