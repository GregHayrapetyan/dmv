from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClientReview, Contact, ContactInfo, Partner, MainBanner, 
    HowItWorks, HowItWorksStep, PricingPlan, PlanFeature,
    TrustSafety, TrustSafetyFeature
)


class PlanFeatureInline(admin.TabularInline):
    """
    Inline admin for plan features.
    """
    model = PlanFeature
    extra = 1
    fields = ('text', 'is_included', 'icon_type', 'icon', 'detail_text', 'order')
    ordering = ('order',)


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pricing plans.
    """
    list_display = (
        "title",
        "subtitle",
        "price_display",
        "features_count",
        "is_featured",
        "is_active",
        "order",
        "created_at",
    )
    
    list_editable = (
        "is_featured",
        "is_active",
        "order",
    )
    
    list_filter = (
        "is_featured",
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "title",
        "subtitle",
        "description",
    )
    
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Plan Information", {
            "fields": ("subtitle", "title", "description")
        }),
        ("Pricing", {
            "fields": ("price_old", "price_period", "price_new", "discount_amount")
        }),
        ("Call to Action", {
            "fields": ("button_text", "button_url")
        }),
        ("Stripe Integration", {
            "fields": ("stripe_price_id_monthly", "stripe_price_id_one_time"),
            "classes": ("collapse",)
        }),
        ("Display Settings", {
            "fields": ("is_featured", "order", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [PlanFeatureInline]
    
    def price_display(self, obj):
        """
        Display pricing information.
        """
        if obj.price_old:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span> → <strong>${}</strong>',
                obj.price_old,
                obj.price_new
            )
        return format_html('<strong>${}</strong>', obj.price_new)
    
    price_display.short_description = "Price"
    
    def features_count(self, obj):
        """
        Display the number of features in this plan.
        """
        count = obj.features.count()
        included = obj.features.filter(is_included=True).count()
        return format_html('<strong>{}</strong> features ({} included)', count, included)
    
    features_count.short_description = "Features"


@admin.register(ClientReview)
class ClientReviewAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "job_title",
        "rating_display",
        "avatar_preview",
        "image_preview",
        "order",
        "is_active",
        "created_at",
    )
    
    list_editable = (
        "order",
        "is_active",
    )
    
    list_filter = (
        "rating",
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "name",
        "job_title",
        "review_text",
    )
    
    readonly_fields = (
        "avatar_preview",
        "avatar_dimensions",
        "image_preview",
        "image_dimensions",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Client Information", {
            "fields": ("name", "job_title", "avatar", "avatar_preview", "avatar_dimensions"),
            "description": "Avatar image (minimum dimensions: 112x112 pixels)"
        }),
        ("Review Image", {
            "fields": ("image", "image_preview", "image_dimensions"),
            "description": "Optional review image (minimum dimensions: 800x600 pixels)"
        }),
        ("Review Details", {
            "fields": ("rating", "review_text")
        }),
        ("Display Settings", {
            "fields": ("order", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def avatar_preview(self, obj):
        """
        Display a thumbnail preview of the avatar image.
        """
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "No avatar"
    
    avatar_preview.short_description = "Avatar Preview"
    
    def avatar_dimensions(self, obj):
        """
        Display the actual dimensions of the uploaded avatar image.
        """
        if obj.avatar:
            try:
                from PIL import Image
                img = Image.open(obj.avatar.path)
                width, height = img.size
                
                # Check if dimensions meet minimum requirements
                if width >= 112 and height >= 112:
                    color = "green"
                    status = "✓"
                else:
                    color = "red"
                    status = "✗"
                
                return format_html(
                    '<span style="color: {};">{} {}x{} pixels</span>',
                    color,
                    status,
                    width,
                    height
                )
            except Exception:
                return "Unable to read dimensions"
        return "No avatar uploaded"
    
    avatar_dimensions.short_description = "Avatar Dimensions"
    
    def rating_display(self, obj):
        """
        Display rating as stars.
        """
        stars = "⭐" * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    
    rating_display.short_description = "Rating"
    
    def image_preview(self, obj):
        """
        Display a thumbnail preview of the review image.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 75px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    
    image_preview.short_description = "Review Image"
    
    def image_dimensions(self, obj):
        """
        Display the actual dimensions of the uploaded review image.
        """
        if obj.image:
            try:
                from PIL import Image
                img = Image.open(obj.image.path)
                width, height = img.size
                
                # Check if dimensions meet minimum requirements
                if width >= 800 and height >= 600:
                    color = "green"
                    status = "✓"
                else:
                    color = "red"
                    status = "✗"
                
                return format_html(
                    '<span style="color: {};">{} {}x{} pixels</span>',
                    color,
                    status,
                    width,
                    height
                )
            except Exception:
                return "Unable to read dimensions"
        return "No image uploaded"
    
    image_dimensions.short_description = "Image Dimensions"


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """
    Admin interface for managing contact information.
    Only one active ContactInfo should exist at a time.
    """
    list_display = (
        "email_primary",
        "phone_primary",
        "is_active",
        "updated_at",
    )
    
    list_filter = (
        "is_active",
        "updated_at",
    )
    
    search_fields = (
        "address_line1",
        "address_line2",
        "email_primary",
        "email_secondary",
        "phone_primary",
        "phone_secondary",
    )
    
    fieldsets = (
        ("Address Information", {
            "fields": ("address_line1", "address_line2")
        }),
        ("Phone Numbers", {
            "fields": ("phone_primary", "phone_secondary")
        }),
        ("Email Addresses", {
            "fields": ("email_primary", "email_secondary")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of contact info to maintain at least one record.
        """
        if ContactInfo.objects.count() <= 1:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Admin interface for managing contact form submissions.
    """
    list_display = (
        "name",
        "email",
        "phone",
        "status",
        "created_at",
    )
    
    list_filter = (
        "status",
        "created_at",
    )
    
    search_fields = (
        "name",
        "email",
        "phone",
        "message",
    )
    
    readonly_fields = (
        "name",
        "email",
        "phone",
        "message",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Message", {
            "fields": ("message",)
        }),
        ("Status", {
            "fields": ("status",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    list_editable = ("status",)
    
    def has_add_permission(self, request):
        """
        Disable adding contacts through admin (they come from the API).
        """
        return False


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """
    Admin interface for managing partners/sponsors.
    """
    list_display = (
        "id",
        "logo_preview",
        "description_preview",
        "order",
        "is_active",
        "created_at",
    )
    
    list_editable = (
        "order",
        "is_active",
    )
    
    list_filter = (
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "description",
    )
    
    readonly_fields = (
        "logo_preview",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Partner Information", {
            "fields": ("logo", "logo_preview", "description", "website_url")
        }),
        ("Display Settings", {
            "fields": ("order", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def logo_preview(self, obj):
        """
        Display a thumbnail preview of the partner logo.
        """
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 60px; object-fit: contain;" />',
                obj.logo.url
            )
        return "No logo"
    
    logo_preview.short_description = "Logo Preview"
    
    def description_preview(self, obj):
        """
        Display truncated description.
        """
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    
    description_preview.short_description = "Description"


@admin.register(MainBanner)
class MainBannerAdmin(admin.ModelAdmin):
    """
    Admin interface for managing main banner content.
    """
    list_display = (
        "title",
        "image_preview",
        "description_preview",
        "is_active",
        "created_at",
    )
    
    list_editable = (
        "is_active",
    )
    
    list_filter = (
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "title",
        "title2",
        "description",
        "stat_text1",
        "stat_text2",
        "button_name",
    )
    
    readonly_fields = (
        "image_preview",
        "image_dimensions",
        "video_preview",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Content", {
            "fields": ("title", "title2", "description")
        }),
        ("Statistics", {
            "fields": ("stat_text1", "stat_text2"),
            "description": "Optional statistics text (e.g., '2200+ Success attempts')"
        }),
        ("Button", {
            "fields": ("button_name", "button_link"),
            "description": "Call-to-action button. Button link is required when 'Use video as button link' is unchecked."
        }),
        ("Video", {
            "fields": ("video", "video_preview", "use_video_as_button_link"),
            "description": "Video file (webm format only). Check 'Use video as button link' to require video upload. Uncheck to require button link instead."
        }),
        ("Image", {
            "fields": ("image", "image_preview", "image_dimensions"),
            "description": "Image must be at least 1108x1206 pixels"
        }),
        ("Display Settings", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def image_preview(self, obj):
        """
        Display a thumbnail preview of the main banner image.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; object-fit: contain;" />',
                obj.image.url
            )
        return "No image"
    
    image_preview.short_description = "Image Preview"
    
    def image_dimensions(self, obj):
        """
        Display the actual dimensions of the uploaded image.
        """
        if obj.image:
            try:
                from PIL import Image
                img = Image.open(obj.image.path)
                width, height = img.size
                
                # Check if dimensions meet minimum requirements
                if width >= 1108 and height >= 1206:
                    color = "green"
                    status = "✓"
                else:
                    color = "red"
                    status = "✗"
                
                return format_html(
                    '<span style="color: {};">{} {}x{} pixels</span>',
                    color,
                    status,
                    width,
                    height
                )
            except Exception:
                return "Unable to read dimensions"
        return "No image uploaded"
    
    image_dimensions.short_description = "Image Dimensions"
    
    def description_preview(self, obj):
        """
        Display truncated description.
        """
        if len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description
    
    description_preview.short_description = "Description"
    
    def video_preview(self, obj):
        """
        Display video player preview or link.
        """
        if obj.video:
            return format_html(
                '<video width="320" height="240" controls><source src="{}" type="video/mp4">Your browser does not support the video tag.</video><br><small>URL: {}</small>',
                obj.video.url,
                obj.video.url
            )
        return "No video uploaded"
    
    video_preview.short_description = "Video Preview"


class HowItWorksStepInline(admin.TabularInline):
    """
    Inline admin for How It Works steps.
    """
    model = HowItWorksStep
    extra = 1
    fields = ('step_number', 'title', 'description', 'icon', 'order')
    ordering = ('order',)


@admin.register(HowItWorks)
class HowItWorksAdmin(admin.ModelAdmin):
    """
    Admin interface for managing How It Works section.
    """
    list_display = (
        "title",
        "section_header",
        "background_preview",
        "steps_count",
        "is_active",
        "created_at",
    )
    
    list_editable = (
        "is_active",
    )
    
    list_filter = (
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "section_header",
        "title",
        "description",
    )
    
    readonly_fields = (
        "background_preview",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Content", {
            "fields": ("section_header", "title", "description")
        }),
        ("Background Image", {
            "fields": ("background_image", "background_preview"),
        }),
        ("Display Settings", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [HowItWorksStepInline]
    
    def background_preview(self, obj):
        """
        Display a thumbnail preview of the background image.
        """
        if obj.background_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; object-fit: cover;" />',
                obj.background_image.url
            )
        return "No background image"
    
    background_preview.short_description = "Background Preview"
    
    def steps_count(self, obj):
        """
        Display the number of steps in this section.
        """
        count = obj.steps.count()
        return format_html('<strong>{}</strong> steps', count)
    
    steps_count.short_description = "Steps"


class TrustSafetyFeatureInline(admin.TabularInline):
    """
    Inline admin for Trust & Safety features.
    """
    model = TrustSafetyFeature
    extra = 1
    fields = ('number', 'title', 'description', 'order')
    ordering = ('order',)


@admin.register(TrustSafety)
class TrustSafetyAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Trust & Safety section.
    """
    list_display = (
        "title",
        "section_header",
        "image_preview",
        "features_count",
        "is_active",
        "created_at",
    )
    
    list_editable = (
        "is_active",
    )
    
    list_filter = (
        "is_active",
        "created_at",
    )
    
    search_fields = (
        "section_header",
        "title",
        "button_text",
    )
    
    readonly_fields = (
        "image_preview",
        "image_dimensions",
        "video_preview",
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Content", {
            "fields": ("section_header", "title")
        }),
        ("Image", {
            "fields": ("image", "image_preview", "image_dimensions"),
            "description": "Image must be at least 800x600 pixels"
        }),
        ("Video", {
            "fields": ("video", "video_preview"),
            "description": "Optional video file (webm or mp4 format)"
        }),
        ("Button", {
            "fields": ("button_text", "button_link"),
            "description": "Call-to-action button"
        }),
        ("Display Settings", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [TrustSafetyFeatureInline]
    
    def image_preview(self, obj):
        """
        Display a thumbnail preview of the Trust & Safety image.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px; object-fit: contain;" />',
                obj.image.url
            )
        return "No image"
    
    image_preview.short_description = "Image Preview"
    
    def image_dimensions(self, obj):
        """
        Display the actual dimensions of the uploaded image.
        """
        if obj.image:
            try:
                from PIL import Image
                img = Image.open(obj.image.path)
                width, height = img.size
                
                # Check if dimensions meet minimum requirements
                if width >= 800 and height >= 600:
                    color = "green"
                    status = "✓"
                else:
                    color = "red"
                    status = "✗"
                
                return format_html(
                    '<span style="color: {};">{} {}x{} pixels</span>',
                    color,
                    status,
                    width,
                    height
                )
            except Exception:
                return "Unable to read dimensions"
        return "No image uploaded"
    
    image_dimensions.short_description = "Image Dimensions"
    
    def video_preview(self, obj):
        """
        Display video player preview or link.
        """
        if obj.video:
            return format_html(
                '<video width="320" height="240" controls><source src="{}" type="video/mp4">Your browser does not support the video tag.</video><br><small>URL: {}</small>',
                obj.video.url,
                obj.video.url
            )
        return "No video uploaded"
    
    video_preview.short_description = "Video Preview"
    
    def features_count(self, obj):
        """
        Display the number of features in this section.
        """
        count = obj.features.count()
        return format_html('<strong>{}</strong> features', count)
    
    features_count.short_description = "Features"

