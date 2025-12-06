from django.contrib import admin
from .models import LessonCategory, Lesson, TestCategory, Test, Question, AnswerOption


@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'lesson_type', 'slug')
    list_filter = ('lesson_type', 'category')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('category',)


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'lesson_category', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('lesson_category',)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('text', 'order', 'points')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'lesson', 'test_category', 'is_demo', 'time_limit_seconds')
    list_filter = ('is_demo', 'test_category')
    search_fields = ('title', 'lesson__title')
    raw_id_fields = ('lesson', 'test_category')
    inlines = [QuestionInline]


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2
    fields = ('text', 'is_correct', 'order', 'explanation')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_preview', 'test', 'order', 'points')
    list_filter = ('test__test_category',)
    search_fields = ('text', 'test__title')
    raw_id_fields = ('test',)
    inlines = [AnswerOptionInline]

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question'


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text_preview', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')
    raw_id_fields = ('question',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Answer'

