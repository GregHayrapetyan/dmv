"""
Wagtail admin customizations and ModelAdmin registrations.
This file integrates existing Django models into the Wagtail admin interface.
"""
from django.contrib import admin
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from wagtail_modeladmin.helpers import PermissionHelper
from wagtail import hooks
from wagtail.documents.models import Document
from wagtail.images.models import Image
from taggit.models import Tag

# Import learning models
from learning.models import (
    LessonCategory, Lesson, Test, Question, AnswerOption,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson
)

# Import site_details models
from site_details.models import (
    PricingPlan, PlanFeature, ClientReview, ContactInfo, Contact, Partner, MainBanner
)


# ============================================================================
# LEARNING SYSTEM - ModelAdmin Classes
# ============================================================================

class LessonCategoryAdmin(ModelAdmin):
    model = LessonCategory
    menu_label = 'Lesson Categories'
    menu_icon = 'folder-open-inverse'
    list_display = ('name',)
    search_fields = ('name',)


class LessonAdmin(ModelAdmin):
    model = Lesson
    menu_label = 'Lessons'
    menu_icon = 'doc-full-inverse'
    list_display = ('title', 'category', 'order', 'is_published', 'duration_minutes', 'created_at')
    list_filter = ('is_published', 'category', 'states')
    search_fields = ('title', 'content')
    ordering = ('order', 'id')


class TestAdmin(ModelAdmin):
    model = Test
    menu_label = 'Tests'
    menu_icon = 'form'
    list_display = ('title', 'is_demo', 'question_count', 'passing_percentage', 'time_limit_seconds', 'created_at')
    list_filter = ('is_demo', 'states', 'vehicles')
    search_fields = ('title', 'description')
    
    def question_count(self, obj):
        """Display the number of questions in this test."""
        count = obj.questions.count()
        return f"{count} question{'s' if count != 1 else ''}"
    question_count.short_description = 'Questions'


class QuestionAdmin(ModelAdmin):
    model = Question
    menu_label = 'Questions'
    menu_icon = 'help'
    list_display = ('text_preview', 'test', 'question_type', 'answer_count', 'order')
    list_filter = ('question_type', 'test')
    search_fields = ('text',)
    ordering = ('test', 'order')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question'
    
    def answer_count(self, obj):
        """Display the number of answer options for this question."""
        count = obj.answer_options.count()
        correct_count = obj.answer_options.filter(is_correct=True).count()
        return f"{count} answers ({correct_count} correct)"
    answer_count.short_description = 'Answers'


class AnswerOptionAdmin(ModelAdmin):
    model = AnswerOption
    menu_label = 'Answer Options'
    menu_icon = 'list-ul'
    list_display = ('text_preview', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('text', 'explanation')
    ordering = ('question', 'order')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Answer'


class LessonProgressAdmin(ModelAdmin):
    model = LessonProgress
    menu_label = 'Lesson Progress'
    menu_icon = 'tasks'
    list_display = ('user', 'lesson', 'completed', 'started_at', 'completed_at')
    list_filter = ('completed',)
    search_fields = ('user__email', 'lesson__title')
    ordering = ('-started_at',)


class TestAttemptAdmin(ModelAdmin):
    model = TestAttempt
    menu_label = 'Test Attempts'
    menu_icon = 'tick-inverse'
    list_display = ('user', 'test', 'percentage', 'passed', 'started_at')
    list_filter = ('passed',)
    search_fields = ('user__email', 'test__title')
    ordering = ('-started_at',)


class FavoriteLessonAdmin(ModelAdmin):
    model = FavoriteLesson
    menu_label = 'Favorite Lessons'
    menu_icon = 'star'
    list_display = ('user', 'lesson', 'created_at')
    search_fields = ('user__email', 'lesson__title')
    ordering = ('-created_at',)


# ============================================================================
# SITE DETAILS - ModelAdmin Classes
# ============================================================================

class PricingPlanAdmin(ModelAdmin):
    model = PricingPlan
    menu_label = 'Pricing Plans'
    menu_icon = 'tag'
    list_display = ('title', 'price_new', 'is_featured', 'is_active', 'order')
    list_filter = ('is_featured', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('order',)


class PlanFeatureAdmin(ModelAdmin):
    model = PlanFeature
    menu_label = 'Plan Features'
    menu_icon = 'list-ul'
    list_display = ('text_preview', 'plan', 'is_included', 'order')
    list_filter = ('is_included', 'plan')
    search_fields = ('text', 'detail_text')
    ordering = ('plan', 'order')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Feature'


class ClientReviewAdmin(ModelAdmin):
    model = ClientReview
    menu_label = 'Client Reviews'
    menu_icon = 'openquote'
    list_display = ('name', 'job_title', 'rating', 'is_active', 'order', 'created_at')
    list_filter = ('rating', 'is_active')
    search_fields = ('name', 'job_title', 'review_text')
    ordering = ('order', '-created_at')


class ContactInfoAdmin(ModelAdmin):
    model = ContactInfo
    menu_label = 'Contact Information'
    menu_icon = 'site'
    list_display = ('email_primary', 'phone_primary', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('email_primary', 'phone_primary', 'address_line1')


class ContactAdmin(ModelAdmin):
    model = Contact
    menu_label = 'Contact Messages'
    menu_icon = 'mail'
    list_display = ('name', 'email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'message')
    ordering = ('-created_at',)


class PartnerAdmin(ModelAdmin):
    model = Partner
    menu_label = 'Partners'
    menu_icon = 'group'
    list_display = ('id', 'description_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('description',)
    ordering = ('order', '-created_at')
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'


class MainBannerAdmin(ModelAdmin):
    model = MainBanner
    menu_label = 'Main Banner'
    menu_icon = 'image'
    list_display = ('title', 'description_preview', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    
    def description_preview(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_preview.short_description = 'Description'


# ============================================================================
# MODEL ADMIN GROUPS
# ============================================================================

class LearningGroup(ModelAdminGroup):
    menu_label = 'Learning System'
    menu_icon = 'education'
    menu_order = 200
    items = (
        LessonCategoryAdmin,
        LessonAdmin,
        TestAdmin,
        QuestionAdmin,
        AnswerOptionAdmin,
    )


class SiteDetailsGroup(ModelAdminGroup):
    menu_label = 'Site Details'
    menu_icon = 'cog'
    menu_order = 300
    items = (
        MainBannerAdmin,
        PricingPlanAdmin,
        PlanFeatureAdmin,
        ClientReviewAdmin,
        ContactInfoAdmin,
        ContactAdmin,
        PartnerAdmin,
    )


# Register the groups
modeladmin_register(LearningGroup)
modeladmin_register(SiteDetailsGroup)


# ============================================================================
# CUSTOM WAGTAIL HOOKS
# ============================================================================

@hooks.register('construct_main_menu')
def hide_default_pages_menu_item(request, menu_items):
    """
    Customize the main menu - hide Documents, Images, and Tags menu items.
    """
    menu_items[:] = [item for item in menu_items if item.name not in ['documents', 'images', 'tags']]


@hooks.register('construct_homepage_panels')
def add_custom_panels(request, panels):
    """
    Add custom panels to the Wagtail admin homepage.
    """
    # You can add custom dashboard panels here
    pass


# ============================================================================
# UNREGISTER WAGTAIL MODELS FROM DJANGO ADMIN
# ============================================================================

# Unregister Wagtail models from the regular Django admin
try:
    admin.site.unregister(Document)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Image)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Tag)
except admin.sites.NotRegistered:
    pass
