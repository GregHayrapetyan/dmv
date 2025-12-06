from django.contrib import admin
from .models import (
    LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer
)


@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'lesson_type', 'order', 'is_published', 'duration_minutes', 'created_at')
    list_filter = ('lesson_type', 'category', 'is_published')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('category',)
    list_editable = ('order', 'is_published')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson_category', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('lesson_category',)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'question_type', 'order', 'points')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'lesson', 'test_category', 'is_demo', 'passing_percentage', 'time_limit_seconds', 'created_at')
    list_filter = ('is_demo', 'test_category', 'shuffle_questions')
    search_fields = ('title', 'lesson__title')
    raw_id_fields = ('lesson', 'test_category')
    inlines = [QuestionInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson', 'test_category', 'title', 'description', 'is_demo')
        }),
        ('Test Settings', {
            'fields': ('passing_percentage', 'max_attempts', 'time_limit_seconds', 'shuffle_questions', 'shuffle_answers')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2
    fields = ('text', 'is_correct', 'order', 'explanation')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_preview', 'test', 'question_type', 'order', 'points', 'has_correct_answer')
    list_filter = ('test__test_category', 'question_type')
    search_fields = ('text', 'test__title')
    raw_id_fields = ('test',)
    inlines = [AnswerOptionInline]
    readonly_fields = ('created_at', 'updated_at')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question'


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_preview', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')
    raw_id_fields = ('question',)
    readonly_fields = ('created_at', 'updated_at')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Answer'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'lesson', 'completed', 'started_at', 'completed_at')
    list_filter = ('completed', 'lesson__category')
    search_fields = ('user__email', 'lesson__title')
    raw_id_fields = ('user', 'lesson')
    readonly_fields = ('started_at', 'updated_at')
    date_hierarchy = 'started_at'


class TestAnswerInline(admin.TabularInline):
    model = TestAnswer
    extra = 0
    fields = ('question', 'selected_option', 'is_correct')
    readonly_fields = ('question', 'selected_option', 'is_correct')
    can_delete = False


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'score', 'total_points', 'percentage', 'passed', 'started_at', 'completed_at')
    list_filter = ('passed', 'test__test_category', 'started_at')
    search_fields = ('user__email', 'test__title')
    raw_id_fields = ('user', 'test')
    readonly_fields = ('started_at', 'completed_at', 'score', 'total_points', 'percentage', 'passed')
    date_hierarchy = 'started_at'
    inlines = [TestAnswerInline]

    def has_add_permission(self, request):
        # Test attempts should only be created through the API
        return False


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_option', 'is_correct')
    list_filter = ('is_correct', 'attempt__test')
    search_fields = ('attempt__user__email', 'question__text')
    raw_id_fields = ('attempt', 'question', 'selected_option')
    readonly_fields = ('attempt', 'question', 'selected_option', 'is_correct')

    def has_add_permission(self, request):
        # Test answers should only be created through the API
        return False

