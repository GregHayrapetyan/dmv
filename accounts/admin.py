from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailOTP, Subscription


@admin.register(User)
class UAdmin(BaseUserAdmin):
    list_display = ("id", "email", "first_name", "last_name", "phone", "is_email_verified", "is_active", "is_staff")
    list_filter = ("is_email_verified", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)
    
    # Fields to display when editing a user
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_email_verified", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    
    # Fields to display when creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "phone", "is_email_verified", "is_staff"),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-verify email for users created via admin panel."""
        if not change:  # New user being created
            obj.is_email_verified = True
        super().save_model(request, obj, form, change)


@admin.register(EmailOTP)
class EAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "code", "is_used", "expires_at")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "current_period_end", "cancel_at_period_end", "created_at")
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("user__email", "stripe_customer_id", "stripe_subscription_id")
    readonly_fields = ("stripe_customer_id", "stripe_subscription_id", "created_at", "updated_at")
    
    fieldsets = (
        ("User", {
            "fields": ("user",)
        }),
        ("Stripe Information", {
            "fields": ("stripe_customer_id", "stripe_subscription_id", "status")
        }),
        ("Subscription Period", {
            "fields": ("current_period_start", "current_period_end", "cancel_at_period_end")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )