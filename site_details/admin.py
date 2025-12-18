from django.contrib import admin
from django.utils.html import format_html
from .models import PricingPlan, PlanFeature, ClientReview, Contact, ContactInfo


class PlanFeatureInline(admin.TabularInline):
    """
    Inline admin for managing plan features within the pricing plan admin.
    """
    model = PlanFeature
    extra = 1
    fields = ("text", "is_included", "icon_type", "icon", "detail_text", "order")
    readonly_fields = ("icon_preview",)
    ordering = ("order",)
    
    def icon_preview(self, obj):
        """
        Display a thumbnail preview of the uploaded icon.
        """
        if obj.icon:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; object-fit: contain;" />',
                obj.icon.url
            )
        return "No custom icon"
    
    icon_preview.short_description = "Icon Preview"


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pricing plans.
    Allows editing plan details and features inline.
    """
    list_display = (
        "title",
        "subtitle",
        "price_display",
        "discount_display",
        "is_featured",
        "order",
        "is_active",
        "feature_count",
    )
    
    list_editable = (
        "is_featured",
        "order",
        "is_active",
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
            "fields": (
                ("price_old", "price_period"),
                "price_new",
                "discount_amount",
            ),
            "description": "Price old is crossed out (e.g., $49 /month). Price new is the current price (e.g., $39)."
        }),
        ("Call to Action", {
            "fields": ("button_text", "button_url")
        }),
        ("Stripe Integration", {
            "fields": (
                "stripe_price_id_monthly",
                "stripe_price_id_one_time",
            ),
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
        Display formatted pricing information.
        Shows old price (crossed out) and new price.
        """
        if obj.price_old:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">${}</span> {} → <strong style="color: #2e7d32;">${}</strong>',
                obj.price_old,
                obj.price_period,
                obj.price_new
            )
        return format_html(
            '<strong>${}</strong> {}',
            obj.price_new,
            obj.price_period
        )
    
    price_display.short_description = "Pricing"
    
    def discount_display(self, obj):
        """
        Display discount amount if available.
        """
        if obj.discount_amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">Save ${}</span>',
                int(obj.discount_amount)
            )
        return "-"
    
    discount_display.short_description = "Discount"
    
    def feature_count(self, obj):
        """
        Display the number of features in this plan.
        """
        count = obj.features.count()
        return format_html(
            '<span style="color: #666;">{} feature{}</span>',
            count,
            "s" if count != 1 else ""
        )
    
    feature_count.short_description = "Features"


@admin.register(ClientReview)
class ClientReviewAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "job_title",
        "rating_display",
        "avatar_preview",
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
        "created_at",
        "updated_at",
    )
    
    fieldsets = (
        ("Client Information", {
            "fields": ("name", "job_title", "avatar", "avatar_preview")
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
    
    def rating_display(self, obj):
        """
        Display rating as stars.
        """
        stars = "⭐" * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    
    rating_display.short_description = "Rating"


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

