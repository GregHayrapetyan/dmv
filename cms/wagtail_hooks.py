"""
Wagtail admin customizations and ModelAdmin registrations.
This file integrates existing Django models into the Wagtail admin interface.
"""
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from wagtail_modeladmin.helpers import PermissionHelper, ButtonHelper
from wagtail import hooks
from wagtail.documents.models import Document
from wagtail.images.models import Image
from taggit.models import Tag

# Import learning models
from learning.models import (
    LessonCategory, Lesson,
    LessonProgress, TestAttempt, TestAnswer, FavoriteLesson
)

# Import CMS models for test management
from cms.models import CMSTest

# Import site_details models
from site_details.models import (
    PricingPlan, PlanFeature, ClientReview, ContactInfo, Contact, Partner, MainBanner, HowItWorks, HowItWorksStep,
    TrustSafety, TrustSafetyFeature, SuccessSteps, SuccessStep
)

# Import accounts models
from accounts.models import Subscription


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


class CMSTestAdmin(ModelAdmin):
    """Test admin with inline question and answer editing."""
    model = CMSTest
    menu_label = 'Tests'
    menu_icon = 'form'
    list_display = ('title', 'question_count', 'passing_percentage', 'time_limit_seconds', 'created_at')
    search_fields = ('title', 'description')
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('description'),
                    FieldPanel('image'),
                ], heading='Basic Information'),
                ObjectList([
                    FieldPanel('passing_percentage'),
                    FieldPanel('max_attempts'),
                    FieldPanel('time_limit_seconds'),
                    FieldPanel('shuffle_questions'),
                    FieldPanel('shuffle_answers'),
                ], heading='Test Settings'),
                ObjectList([
                    InlinePanel('questions', label="Questions"),
                ], heading='Questions'),
            ])
        return self.edit_handler
    
    def question_count(self, obj):
        """Display the number of questions in this test."""
        count = obj.questions.count()
        return f"{count} question{'s' if count != 1 else ''}"
    question_count.short_description = 'Questions'


# Questions and Answers are managed inline within CMSTest


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
    """Pricing Plan admin with inline feature editing."""
    model = PricingPlan
    menu_label = 'Pricing Plans'
    menu_icon = 'tag'
    list_display = ('title', 'price_new', 'feature_count', 'is_featured', 'is_active', 'order')
    list_filter = ('is_featured', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('order',)
    
    def feature_count(self, obj):
        """Display the number of features in this plan."""
        count = obj.features.count()
        return f"{count} feature{'s' if count != 1 else ''}"
    feature_count.short_description = 'Features'


class ClientReviewAdmin(ModelAdmin):
    model = ClientReview
    menu_label = 'Client Reviews'
    menu_icon = 'openquote'
    list_display = ('name', 'job_title', 'rating', 'avatar_preview', 'image_preview', 'is_active', 'created_at')
    list_filter = ('rating', 'is_active')
    search_fields = ('name', 'job_title', 'review_text')
    ordering = ('order', '-created_at')
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    MultiFieldPanel([
                        FieldPanel('name'),
                        FieldPanel('job_title'),
                    ], heading='Client Information'),
                    MultiFieldPanel([
                        FieldPanel('avatar'),
                        FieldPanel('image'),
                    ], heading='Images'),
                    MultiFieldPanel([
                        FieldPanel('rating'),
                        FieldPanel('review_text'),
                    ], heading='Review Details'),
                    FieldPanel('is_active'),
                ], heading='Content'),
            ])
        return self.edit_handler
    
    def avatar_preview(self, obj):
        """Display a thumbnail preview of the avatar image."""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return '-'
    avatar_preview.short_description = 'Avatar'
    
    def image_preview(self, obj):
        """Display a thumbnail preview of the review image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 45px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Review Image'


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


class HowItWorksAdmin(ModelAdmin):
    """How It Works admin with inline step editing."""
    model = HowItWorks
    menu_label = 'How It Works'
    menu_icon = 'list-ol'
    list_display = ('title', 'section_header', 'steps_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'section_header', 'description')
    ordering = ('-created_at',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('background_image'),
                ], heading='Background'),
                ObjectList([
                    FieldPanel('section_header'),
                    FieldPanel('title'),
                    FieldPanel('description'),
                ], heading='Content'),
                ObjectList([
                    InlinePanel('steps', label="Steps"),
                ], heading='Steps'),
                ObjectList([
                    FieldPanel('is_active'),
                ], heading='Display Settings'),
            ])
        return self.edit_handler
    
    def steps_count(self, obj):
        """Display the number of steps in this section."""
        count = obj.steps.count()
        return format_html('<strong>{}</strong> steps', count)
    steps_count.short_description = 'Steps'


class TrustSafetyAdmin(ModelAdmin):
    """Trust & Safety admin with inline feature editing."""
    model = TrustSafety
    menu_label = 'Trust & Safety'
    menu_icon = 'shield'
    list_display = ('title', 'section_header', 'features_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'section_header', 'button_text')
    ordering = ('-created_at',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('section_header'),
                    FieldPanel('title'),
                ], heading='Content'),
                ObjectList([
                    FieldPanel('image'),
                ], heading='Image'),
                ObjectList([
                    FieldPanel('video'),
                ], heading='Video'),
                ObjectList([
                    FieldPanel('button_text'),
                    FieldPanel('button_link'),
                ], heading='Button'),
                ObjectList([
                    InlinePanel('features', label="Features"),
                ], heading='Features'),
                ObjectList([
                    FieldPanel('is_active'),
                ], heading='Display Settings'),
            ])
        return self.edit_handler
    
    def features_count(self, obj):
        """Display the number of features in this section."""
        count = obj.features.count()
        return format_html('<strong>{}</strong> features', count)
    features_count.short_description = 'Features'


class SuccessStepsAdmin(ModelAdmin):
    """Success Steps admin with inline step editing."""
    model = SuccessSteps
    menu_label = 'Success Steps'
    menu_icon = 'success'
    list_display = ('title', 'button_text', 'steps_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description', 'button_text')
    ordering = ('-created_at',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('description'),
                ], heading='Content'),
                ObjectList([
                    FieldPanel('button_text'),
                    FieldPanel('button_link'),
                ], heading='Button'),
                ObjectList([
                    InlinePanel('steps', label="Steps"),
                ], heading='Steps'),
                ObjectList([
                    FieldPanel('is_active'),
                ], heading='Display Settings'),
            ])
        return self.edit_handler
    
    def steps_count(self, obj):
        """Display the number of steps in this section."""
        count = obj.steps.count()
        return format_html('<strong>{}</strong> steps', count)
    steps_count.short_description = 'Steps'


# ============================================================================
# ACCOUNTS - ModelAdmin Classes (for Settings menu)
# ============================================================================

class SubscriptionAdmin(ModelAdmin):
    model = Subscription
    menu_label = 'Subscriptions'
    menu_icon = 'user'
    list_display = ('user', 'status', 'stripe_customer_id', 'current_period_end', 'cancel_at_period_end', 'created_at')
    list_filter = ('status', 'cancel_at_period_end')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id')
    ordering = ('-created_at',)
    
    # Add to Settings menu instead of main menu
    add_to_settings_menu = True


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
        CMSTestAdmin,  # Questions and answers managed inline
    )


class SiteDetailsGroup(ModelAdminGroup):
    menu_label = 'Site Details'
    menu_icon = 'cog'
    menu_order = 300
    items = (
        MainBannerAdmin,
        HowItWorksAdmin,
        SuccessStepsAdmin,
        TrustSafetyAdmin,
        PricingPlanAdmin,
        ClientReviewAdmin,
        ContactInfoAdmin,
        ContactAdmin,
        PartnerAdmin,
    )


# Register the groups
modeladmin_register(LearningGroup)
modeladmin_register(SiteDetailsGroup)

# Register Subscriptions separately (will appear in Settings menu)
modeladmin_register(SubscriptionAdmin)


# ============================================================================
# CUSTOM WAGTAIL HOOKS
# ============================================================================

@hooks.register('construct_main_menu')
def hide_default_pages_menu_item(request, menu_items):
    """
    Customize the main menu - hide Documents, Images, Tags, Reports, Snippets, and Help menu items.
    """
    menu_items[:] = [item for item in menu_items if item.name not in ['documents', 'images', 'tags', 'reports', 'snippets', 'help']]


@hooks.register('construct_settings_menu')
def hide_settings_menu_items(request, menu_items):
    """
    Hide specific items from the Settings menu: Workflows, Workflow tasks, Sites, Collections, and Redirects.
    """
    menu_items[:] = [item for item in menu_items if item.name not in ['workflows', 'workflow-tasks', 'sites', 'collections', 'redirects']]


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
