from django.contrib import admin
from django.utils.html import format_html
from .models import CMSTest, CMSQuestion, CMSAnswer


class CMSAnswerInline(admin.TabularInline):
    """Inline admin for answer options."""
    model = CMSAnswer
    extra = 2
    fields = ('text', 'is_correct', 'explanation', 'order')
    ordering = ('order',)


class CMSQuestionInline(admin.StackedInline):
    """Inline admin for questions."""
    model = CMSQuestion
    extra = 1
    fields = ('text', 'image', 'question_type', 'order')
    ordering = ('order',)
    show_change_link = True


@admin.register(CMSTest)
class CMSTestAdmin(admin.ModelAdmin):
    """Admin interface for managing tests."""
    list_display = (
        "title",
        "questions_count",
        "passing_percentage",
        "time_limit_display",
        "max_attempts_display",
        "created_at",
    )
    
    list_filter = (
        "shuffle_questions",
        "shuffle_answers",
        "created_at",
    )
    
    search_fields = (
        "title",
        "description",
    )
    
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "description", "image")
        }),
        ("Test Settings", {
            "fields": (
                "passing_percentage",
                "time_limit_seconds",
                "max_attempts",
                "shuffle_questions",
                "shuffle_answers",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [CMSQuestionInline]
    
    def questions_count(self, obj):
        """Display the number of questions in this test."""
        count = obj.questions.count()
        return format_html('<strong>{}</strong> questions', count)
    
    questions_count.short_description = "Questions"
    
    def time_limit_display(self, obj):
        """Display time limit in a readable format."""
        if obj.time_limit_seconds:
            minutes = obj.time_limit_seconds // 60
            seconds = obj.time_limit_seconds % 60
            if minutes > 0:
                return f"{minutes}m {seconds}s" if seconds else f"{minutes}m"
            return f"{seconds}s"
        return "No limit"
    
    time_limit_display.short_description = "Time Limit"
    
    def max_attempts_display(self, obj):
        """Display max attempts."""
        return obj.max_attempts if obj.max_attempts else "Unlimited"
    
    max_attempts_display.short_description = "Max Attempts"


@admin.register(CMSQuestion)
class CMSQuestionAdmin(admin.ModelAdmin):
    """Admin interface for managing questions."""
    list_display = (
        "text_preview",
        "test",
        "question_type",
        "answers_count",
        "order",
    )
    
    list_filter = (
        "question_type",
        "test",
    )
    
    search_fields = (
        "text",
        "test__title",
    )
    
    list_editable = ("order",)
    
    fieldsets = (
        ("Question Details", {
            "fields": ("test", "text", "image", "question_type", "order")
        }),
    )
    
    inlines = [CMSAnswerInline]
    
    def text_preview(self, obj):
        """Display truncated question text."""
        if len(obj.text) > 80:
            return f"{obj.text[:80]}..."
        return obj.text
    
    text_preview.short_description = "Question"
    
    def answers_count(self, obj):
        """Display the number of answers."""
        count = obj.answers.count()
        correct = obj.answers.filter(is_correct=True).count()
        return format_html('<strong>{}</strong> answers ({} correct)', count, correct)
    
    answers_count.short_description = "Answers"
