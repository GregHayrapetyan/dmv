from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, Feature


class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1
    fields = ("text", "is_included", "icon", "icon_preview", "order")
    readonly_fields = ("icon_preview",)

    def icon_preview(self, obj):
        """
        Render a small icon preview in the admin interface.
        """
        if not obj.icon:
            return ""
        return format_html('<i class="{}"></i>', obj.icon)

    icon_preview.short_description = "Icon preview"


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subtitle",
        "price_new",
        "is_featured",
        "order",
        "is_active",
    )  # Columns in the list view

    list_editable = (
        "is_featured",
        "order",
        "is_active",
    )  # Editable fields directly in the list view

    inlines = [FeatureInline]  # Manage features on the same page as the plan

