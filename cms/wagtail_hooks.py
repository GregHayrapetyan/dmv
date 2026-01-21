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
    TrustSafety, TrustSafetyFeature, SuccessSteps, SuccessStep, LearningOptions, LearningOption
)

# Import accounts models
from accounts.models import Subscription

# Import onboarding models
from onboarding.models import State, Vehicle


# ============================================================================
# LEARNING SYSTEM - ModelAdmin Classes
# ============================================================================

class LessonCategoryAdmin(ModelAdmin):
    model = LessonCategory
    menu_label = 'Lesson Categories'
    menu_icon = 'folder-open-inverse'
    list_display = ('name',)
    search_fields = ('name',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('name'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('name_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('name_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('name_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('name_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('name_zh'),
                ], heading='Chinese'),
            ])
        return self.edit_handler


class LessonAdmin(ModelAdmin):
    model = Lesson
    menu_label = 'Lessons'
    menu_icon = 'doc-full-inverse'
    list_display = ('title', 'category', 'order', 'is_published', 'duration_minutes', 'created_at')
    list_filter = ('is_published', 'category', 'states')
    search_fields = ('title', 'content')
    ordering = ('order', 'id')
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList, MultiFieldPanel
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('content'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('title_ru'),
                    FieldPanel('content_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('title_hy'),
                    FieldPanel('content_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('title_hi'),
                    FieldPanel('content_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('title_es'),
                    FieldPanel('content_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('title_zh'),
                    FieldPanel('content_zh'),
                ], heading='Chinese'),
                ObjectList([
                    FieldPanel('category'),
                    FieldPanel('video'),
                    FieldPanel('image'),
                    FieldPanel('order'),
                    FieldPanel('is_published'),
                    FieldPanel('duration_minutes'),
                    FieldPanel('states'),
                    FieldPanel('test'),
                ], heading='Settings'),
            ])
        return self.edit_handler


class CMSTestAdmin(ModelAdmin):
    """Test admin with inline question and answer editing."""
    model = CMSTest
    menu_label = 'Tests'
    menu_icon = 'form'
    list_display = ('title', 'question_count', 'passing_percentage', 'time_limit_seconds', 'created_at')
    search_fields = ('title', 'description')
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList, MultiFieldPanel
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('description'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('title_ru'),
                    FieldPanel('description_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('title_hy'),
                    FieldPanel('description_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('title_hi'),
                    FieldPanel('description_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('title_es'),
                    FieldPanel('description_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('title_zh'),
                    FieldPanel('description_zh'),
                ], heading='Chinese'),
                ObjectList([
                    FieldPanel('image'),
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
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList, MultiFieldPanel
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('subtitle'),
                    FieldPanel('title'),
                    FieldPanel('description'),
                    FieldPanel('price_period'),
                    FieldPanel('button_text'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('subtitle_ru'),
                    FieldPanel('title_ru'),
                    FieldPanel('description_ru'),
                    FieldPanel('price_period_ru'),
                    FieldPanel('button_text_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('subtitle_hy'),
                    FieldPanel('title_hy'),
                    FieldPanel('description_hy'),
                    FieldPanel('price_period_hy'),
                    FieldPanel('button_text_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('subtitle_hi'),
                    FieldPanel('title_hi'),
                    FieldPanel('description_hi'),
                    FieldPanel('price_period_hi'),
                    FieldPanel('button_text_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('subtitle_es'),
                    FieldPanel('title_es'),
                    FieldPanel('description_es'),
                    FieldPanel('price_period_es'),
                    FieldPanel('button_text_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('subtitle_zh'),
                    FieldPanel('title_zh'),
                    FieldPanel('description_zh'),
                    FieldPanel('price_period_zh'),
                    FieldPanel('button_text_zh'),
                ], heading='Chinese'),
                ObjectList([
                    InlinePanel('features', label="Features"),
                ], heading='Features'),
                ObjectList([
                    FieldPanel('price_old'),
                    FieldPanel('price_new'),
                    FieldPanel('discount_amount'),
                    FieldPanel('button_url'),
                    FieldPanel('is_featured'),
                    FieldPanel('is_active'),
                    FieldPanel('order'),
                    FieldPanel('stripe_price_id_monthly'),
                    FieldPanel('stripe_price_id_one_time'),
                ], heading='Settings'),
            ])
        return self.edit_handler
    
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
                    FieldPanel('name'),
                    FieldPanel('job_title'),
                    FieldPanel('review_text'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('job_title_ru'),
                    FieldPanel('review_text_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('job_title_hy'),
                    FieldPanel('review_text_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('job_title_hi'),
                    FieldPanel('review_text_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('job_title_es'),
                    FieldPanel('review_text_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('job_title_zh'),
                    FieldPanel('review_text_zh'),
                ], heading='Chinese'),
                ObjectList([
                    FieldPanel('avatar'),
                    FieldPanel('image'),
                    FieldPanel('rating'),
                    FieldPanel('order'),
                    FieldPanel('is_active'),
                ], heading='Settings'),
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
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('title2'),
                    FieldPanel('description'),
                    FieldPanel('stat_text1'),
                    FieldPanel('stat_text2'),
                    FieldPanel('button_name'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('title_ru'),
                    FieldPanel('title2_ru'),
                    FieldPanel('description_ru'),
                    FieldPanel('stat_text1_ru'),
                    FieldPanel('stat_text2_ru'),
                    FieldPanel('button_name_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('title_hy'),
                    FieldPanel('title2_hy'),
                    FieldPanel('description_hy'),
                    FieldPanel('stat_text1_hy'),
                    FieldPanel('stat_text2_hy'),
                    FieldPanel('button_name_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('title_hi'),
                    FieldPanel('title2_hi'),
                    FieldPanel('description_hi'),
                    FieldPanel('stat_text1_hi'),
                    FieldPanel('stat_text2_hi'),
                    FieldPanel('button_name_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('title_es'),
                    FieldPanel('title2_es'),
                    FieldPanel('description_es'),
                    FieldPanel('stat_text1_es'),
                    FieldPanel('stat_text2_es'),
                    FieldPanel('button_name_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('title_zh'),
                    FieldPanel('title2_zh'),
                    FieldPanel('description_zh'),
                    FieldPanel('stat_text1_zh'),
                    FieldPanel('stat_text2_zh'),
                    FieldPanel('button_name_zh'),
                ], heading='Chinese'),
                ObjectList([
                    FieldPanel('image'),
                    FieldPanel('video'),
                    FieldPanel('button_link'),
                    FieldPanel('use_video_as_button_link'),
                    FieldPanel('is_active'),
                ], heading='Settings'),
            ])
        return self.edit_handler
    
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
                    FieldPanel('section_header'),
                    FieldPanel('title'),
                    FieldPanel('description'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('section_header_ru'),
                    FieldPanel('title_ru'),
                    FieldPanel('description_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('section_header_hy'),
                    FieldPanel('title_hy'),
                    FieldPanel('description_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('section_header_hi'),
                    FieldPanel('title_hi'),
                    FieldPanel('description_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('section_header_es'),
                    FieldPanel('title_es'),
                    FieldPanel('description_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('section_header_zh'),
                    FieldPanel('title_zh'),
                    FieldPanel('description_zh'),
                ], heading='Chinese'),
                ObjectList([
                    InlinePanel('steps', label="Steps"),
                ], heading='Steps'),
                ObjectList([
                    FieldPanel('background_image'),
                    FieldPanel('is_active'),
                ], heading='Settings'),
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
                    FieldPanel('button_text'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('section_header_ru'),
                    FieldPanel('title_ru'),
                    FieldPanel('button_text_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('section_header_hy'),
                    FieldPanel('title_hy'),
                    FieldPanel('button_text_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('section_header_hi'),
                    FieldPanel('title_hi'),
                    FieldPanel('button_text_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('section_header_es'),
                    FieldPanel('title_es'),
                    FieldPanel('button_text_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('section_header_zh'),
                    FieldPanel('title_zh'),
                    FieldPanel('button_text_zh'),
                ], heading='Chinese'),
                ObjectList([
                    InlinePanel('features', label="Features"),
                ], heading='Features'),
                ObjectList([
                    FieldPanel('image'),
                    FieldPanel('video'),
                    FieldPanel('button_link'),
                    FieldPanel('is_active'),
                ], heading='Settings'),
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
                    FieldPanel('button_text'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('title_ru'),
                    FieldPanel('description_ru'),
                    FieldPanel('button_text_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('title_hy'),
                    FieldPanel('description_hy'),
                    FieldPanel('button_text_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('title_hi'),
                    FieldPanel('description_hi'),
                    FieldPanel('button_text_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('title_es'),
                    FieldPanel('description_es'),
                    FieldPanel('button_text_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('title_zh'),
                    FieldPanel('description_zh'),
                    FieldPanel('button_text_zh'),
                ], heading='Chinese'),
                ObjectList([
                    InlinePanel('steps', label="Steps"),
                ], heading='Steps'),
                ObjectList([
                    FieldPanel('button_link'),
                    FieldPanel('is_active'),
                ], heading='Settings'),
            ])
        return self.edit_handler
    
    def steps_count(self, obj):
        """Display the number of steps in this section."""
        count = obj.steps.count()
        return format_html('<strong>{}</strong> steps', count)
    steps_count.short_description = 'Steps'


class LearningOptionsAdmin(ModelAdmin):
    """Learning Options admin with inline option editing."""
    model = LearningOptions
    menu_label = 'Learning Options'
    menu_icon = 'view'
    list_display = ('title', 'options_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('title'),
                    FieldPanel('description'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('title_ru'),
                    FieldPanel('description_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('title_hy'),
                    FieldPanel('description_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('title_hi'),
                    FieldPanel('description_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('title_es'),
                    FieldPanel('description_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('title_zh'),
                    FieldPanel('description_zh'),
                ], heading='Chinese'),
                ObjectList([
                    InlinePanel('options', label="Options"),
                ], heading='Options'),
                ObjectList([
                    FieldPanel('is_active'),
                ], heading='Settings'),
            ])
        return self.edit_handler
    
    def options_count(self, obj):
        """Display the number of options in this section."""
        count = obj.options.count()
        return format_html('<strong>{}</strong> options', count)
    options_count.short_description = 'Options'


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
        LearningOptionsAdmin,
        PricingPlanAdmin,
        ClientReviewAdmin,
        ContactInfoAdmin,
        ContactAdmin,
        PartnerAdmin,
    )


# ============================================================================
# ONBOARDING - ModelAdmin Classes
# ============================================================================

class StateAdmin(ModelAdmin):
    model = State
    menu_label = 'States'
    menu_icon = 'site'
    list_display = ('name',)
    search_fields = ('name',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('name'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('name_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('name_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('name_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('name_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('name_zh'),
                ], heading='Chinese'),
            ])
        return self.edit_handler


class VehicleAdmin(ModelAdmin):
    model = Vehicle
    menu_label = 'Vehicles'
    menu_icon = 'car'
    list_display = ('name', 'image')
    search_fields = ('name',)
    
    def get_edit_handler(self):
        from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
        
        if not hasattr(self, 'edit_handler') or self.edit_handler is None:
            self.edit_handler = TabbedInterface([
                ObjectList([
                    FieldPanel('name'),
                ], heading='English'),
                ObjectList([
                    FieldPanel('name_ru'),
                ], heading='Russian'),
                ObjectList([
                    FieldPanel('name_hy'),
                ], heading='Armenian'),
                ObjectList([
                    FieldPanel('name_hi'),
                ], heading='Hindi'),
                ObjectList([
                    FieldPanel('name_es'),
                ], heading='Spanish'),
                ObjectList([
                    FieldPanel('name_zh'),
                ], heading='Chinese'),
                ObjectList([
                    FieldPanel('image'),
                    FieldPanel('image_width'),
                    FieldPanel('image_height'),
                ], heading='Settings'),
            ])
        return self.edit_handler


class OnboardingGroup(ModelAdminGroup):
    menu_label = 'Onboarding'
    menu_icon = 'user'
    menu_order = 350
    items = (
        StateAdmin,
        VehicleAdmin,
    )


# Register the groups
modeladmin_register(LearningGroup)
modeladmin_register(SiteDetailsGroup)
modeladmin_register(OnboardingGroup)

# Register Subscriptions separately (will appear in Settings menu)
modeladmin_register(SubscriptionAdmin)


# ============================================================================
# CUSTOM WAGTAIL HOOKS
# ============================================================================

@hooks.register('construct_main_menu')
def hide_default_pages_menu_item(request, menu_items):
    """
    Customize the main menu - hide docs, Images, Tags, Reports, Snippets, and Help menu items.
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
