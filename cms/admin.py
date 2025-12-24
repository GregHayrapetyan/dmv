from django.contrib import admin
from learning.models import Test, Question, AnswerOption

# Unregister models from learning admin if already registered
try:
    admin.site.unregister(Test)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Question)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(AnswerOption)
except admin.sites.NotRegistered:
    pass


class AnswerOptionInline(admin.TabularInline):
    """Inline admin for answer options within a question."""
    model = AnswerOption
    extra = 2
    fields = ('text', 'is_correct', 'order', 'explanation')
    ordering = ['order']


class QuestionInline(admin.StackedInline):
    """Inline admin for questions within a test."""
    model = Question
    extra = 1
    fields = ('text', 'image', 'video', 'question_type', 'order')
    ordering = ['order']
    show_change_link = True  # Add link to edit question with answers


@admin.register(Test)
class CMSTestAdmin(admin.ModelAdmin):
    """CMS Admin interface for managing tests with questions."""
    
    list_display = ('id', 'title', 'get_lesson', 'passing_percentage', 'time_limit_seconds', 'question_count', 'created_at')
    list_filter = ('shuffle_questions', 'shuffle_answers', 'states', 'vehicles', 'created_at')
    search_fields = ('title', 'description', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at', 'question_count')
    filter_horizontal = ('states', 'vehicles')
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'image')
        }),
        ('Availability', {
            'fields': ('states', 'vehicles'),
            'description': 'Select states and vehicle types for this test. Leave empty for all.'
        }),
        ('Test Settings', {
            'fields': ('passing_percentage', 'max_attempts', 'time_limit_seconds', 'shuffle_questions', 'shuffle_answers')
        }),
        ('Statistics', {
            'fields': ('question_count',),
            'classes': ('collapse',)
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
            return "No lesson assigned"
    get_lesson.short_description = 'Lesson'
    
    def question_count(self, obj):
        """Display the number of questions in this test."""
        if obj.pk:
            return obj.questions.count()
        return 0
    question_count.short_description = 'Number of Questions'


@admin.register(Question)
class CMSQuestionAdmin(admin.ModelAdmin):
    """CMS Admin interface for managing questions with answers."""
    
    list_display = ('id', 'text_preview', 'test', 'question_type', 'order', 'answer_count', 'has_correct_answer', 'created_at')
    list_filter = ('question_type', 'test', 'created_at')
    search_fields = ('text', 'test__title')
    raw_id_fields = ('test',)
    inlines = [AnswerOptionInline]
    readonly_fields = ('created_at', 'updated_at', 'answer_count')
    
    fieldsets = (
        ('Question Content', {
            'fields': ('test', 'text', 'image', 'video', 'question_type')
        }),
        ('Settings', {
            'fields': ('order',)
        }),
        ('Statistics', {
            'fields': ('answer_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show a preview of the question text."""
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    text_preview.short_description = 'Question'
    
    def answer_count(self, obj):
        """Display the number of answer options for this question."""
        if obj.pk:
            return obj.answer_options.count()
        return 0
    answer_count.short_description = 'Number of Answers'


@admin.register(AnswerOption)
class CMSAnswerOptionAdmin(admin.ModelAdmin):
    """CMS Admin interface for managing answer options."""
    
    list_display = ('id', 'text_preview', 'question_preview', 'is_correct', 'order', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('text', 'question__text', 'question__test__title')
    raw_id_fields = ('question',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Answer Content', {
            'fields': ('question', 'text', 'is_correct')
        }),
        ('Settings', {
            'fields': ('order', 'explanation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show a preview of the answer text."""
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Answer'
    
    def question_preview(self, obj):
        """Show a preview of the question this answer belongs to."""
        return obj.question.text[:60] + '...' if len(obj.question.text) > 60 else obj.question.text
    question_preview.short_description = 'Question'
