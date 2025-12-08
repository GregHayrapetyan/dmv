# pricing/models.py
from django.db import models


class IconChoices(models.TextChoices):
    CHECK = "fa-solid fa-check", "Check"
    XMARK = "fa-solid fa-xmark", "Cross"
    STAR  = "fa-solid fa-star", "Star"
    CAR   = "fa-solid fa-car", "Car"
    # Add your own options if needed


class Plan(models.Model):
    subtitle = models.CharField(
        max_length=100,
        blank=True,
    )  # e.g. "STATE-SPECIFIC"

    title = models.CharField(
        max_length=100,
    )  # e.g. "7-Day Express"

    description = models.TextField(
        blank=True,
    )  # Small text under the title

    price_old = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )  # Old price, e.g. 49

    price_new = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )  # New price, e.g. 39

    price_period = models.CharField(
        max_length=50,
        default="/month",
    )  # e.g. "/month"

    save_text = models.CharField(
        max_length=50,
        blank=True,
    )  # e.g. "Save $10"

    badge_text = models.CharField(
        max_length=100,
        blank=True,
    )  # e.g. "Pass Guarantee ..."

    button_text = models.CharField(
        max_length=50,
        default="Start my plan",
    )  # Button label

    button_url = models.URLField(
        blank=True,
    )  # URL for CTA button

    is_featured = models.BooleanField(
        default=False,
    )  # Highlight this plan visually

    order = models.PositiveIntegerField(
        default=0,
    )  # Sort order from left to right

    is_active = models.BooleanField(
        default=True,
    )  # If False, plan is hidden on the public pricing page

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return self.title


class Feature(models.Model):
    plan = models.ForeignKey(
        Plan,
        related_name="features",
        on_delete=models.CASCADE,
    )  # Parent plan

    text = models.CharField(
        max_length=255,
    )  # Feature text

    is_included = models.BooleanField(
        default=True,
    )  # Included in this plan or not

    order = models.PositiveIntegerField(
        default=0,
    )  # Sort order within the plan

    icon = models.CharField(
        max_length=50,
        choices=IconChoices.choices,
        default=IconChoices.CHECK,
        help_text="CSS class for the icon (e.g. FontAwesome)",
    )  # Icon CSS class

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return f"{self.plan.title}: {self.text[:40]}"
