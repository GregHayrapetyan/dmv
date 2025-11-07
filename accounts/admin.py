from django.contrib import admin
from .models import User, EmailOTP


@admin.register(User)
class UAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "is_email_verified")


@admin.register(EmailOTP)
class EAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "code", "is_used", "expires_at")