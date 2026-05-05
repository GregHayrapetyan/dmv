from django.contrib import admin
from .models import (
    LessonCategory, Lesson, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson
)


@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'order', 'is_published', 'duration_minutes', 'test', 'created_at')
    list_filter = ('is_published', 'category', 'states')
    search_fields = ('title',)
    list_editable = ('order', 'is_published')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('states',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'content')
        }),
        ('Media', {
            'fields': ('video', 'image')
        }),
        ('Settings', {
            'fields': ('order', 'is_published', 'duration_minutes', 'test')
        }),
        ('State Availability', {
            'fields': ('states',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'image', 'video', 'question_type', 'order')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'order', 'get_lesson', 'get_vehicles', 'passing_percentage', 'time_limit_seconds', "is_demo", 'mixed_question_count', 'created_at')
    list_filter = ('shuffle_questions', 'states', 'vehicles', "is_demo")
    search_fields = ('title', 'lesson__title')
    inlines = [QuestionInline]
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('states', 'vehicles')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'image')
        }),
        ('English Translation', {
            'fields': ('title_en', 'description_en'),
            'classes': ('collapse',)
        }),
        ('Russian Translation', {
            'fields': ('title_ru', 'description_ru'),
            'classes': ('collapse',)
        }),
        ('Armenian Translation', {
            'fields': ('title_hy', 'description_hy'),
            'classes': ('collapse',)
        }),
        ('Hindi Translation', {
            'fields': ('title_hi', 'description_hi'),
            'classes': ('collapse',)
        }),
        ('Spanish Translation', {
            'fields': ('title_es', 'description_es'),
            'classes': ('collapse',)
        }),
        ('Chinese Translation', {
            'fields': ('title_zh', 'description_zh'),
            'classes': ('collapse',)
        }),
        ('Availability', {
            'fields': ('states', 'vehicles')
        }),
        ('Test Settings', {
            'fields': ('order', 'passing_percentage', 'max_attempts', 'time_limit_seconds', 'is_demo', 'shuffle_questions', 'shuffle_answers')
        }),
        ('Mixed Screening Test', {
            'fields': ('mixed_question_count',),
            'description': 'Number of random questions to pull from this test for the mixed screening test. Set 0 to exclude.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_lesson(self, obj):
        """Get the lesson this test belongs to."""
        try:
            return obj.lesson
        except:
            return None
    get_lesson.short_description = 'Lesson'
    
    def get_vehicles(self, obj):
        """Display vehicle types for this test."""
        vehicles = obj.vehicles.all()
        if vehicles.exists():
            return ", ".join([v.name for v in vehicles])
        return "All vehicles"
    get_vehicles.short_description = 'Vehicle Types'


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2
    fields = ('text', 'is_correct', 'order', 'explanation')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_preview', 'test', 'question_type', 'order', 'has_correct_answer')
    list_filter = ('question_type',)
    search_fields = ('text', 'test__title')
    raw_id_fields = ('test',)
    inlines = [AnswerOptionInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Question Content', {
            'fields': ('test', 'text', 'image', 'video', 'question_type')
        }),
        ('Settings', {
            'fields': ('order',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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
    list_filter = ('completed',)
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
    list_display = ('id', 'user', 'test', 'correct_answers', 'incorrect_answers', 'questions_count', 'percentage', 'passed', 'started_at', 'completed_at')
    list_filter = ('passed', 'started_at')
    search_fields = ('user__email', 'test__title')
    raw_id_fields = ('user', 'test')
    readonly_fields = ('started_at', 'completed_at', 'correct_answers', 'incorrect_answers', 'questions_count', 'percentage', 'passed')
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


@admin.register(FavoriteLesson)
class FavoriteLessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'lesson', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'lesson__title')
    raw_id_fields = ('user', 'lesson')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

