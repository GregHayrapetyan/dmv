from django.contrib import admin
from .models import User, EmailOTP, Subscription


@admin.register(User)
class UAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "is_email_verified")


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