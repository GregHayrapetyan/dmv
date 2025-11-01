from django.contrib import admin

from django.contrib import admin
from .models import User


@admin.register(User)
class UAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "is_email_verified")
