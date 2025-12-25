# site_details/models.py
from django.db import models
from wagtail.models import Orderable
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from PIL import Image


@register_snippet
class PricingPlan(ClusterableModel):
    """
    Pricing plan model for DMV test preparation packages.
    Represents different subscription tiers (e.g., 7-Day Express, 30-Day All-Access).
    """
    
    # Plan identification
    subtitle = models.CharField(
        max_length=100,
        blank=True,
        help_text="Plan category (e.g., 'STATE-SPECIFIC')",
    )
    
    title = models.CharField(
        max_length=100,
        help_text="Plan name (e.g., '7-Day Express', '30-Day All-Access')",
    )
    
    description = models.TextField(
        blank=True,
        help_text="Brief description of the plan",
    )
    
    # Pricing details
    price_old = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Old/original price (crossed out, e.g., $49)",
    )
    
    price_period = models.CharField(
        max_length=50,
        default="/month",
        help_text="Price period text (e.g., '/month')",
    )
    
    price_new = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="New/current price (e.g., $39)",
    )
    
    discount_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Discount amount shown in badge (e.g., 10 for 'Save $10')",
    )
    
    # CTA button
    button_text = models.CharField(
        max_length=50,
        default="Start my plan",
        help_text="Call-to-action button text",
    )
    
    button_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="URL or route for the CTA button",
    )
    
    # Display settings
    is_featured = models.BooleanField(
        default=False,
        help_text="Highlight this plan with a border/special styling",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this plan is visible on the site",
    )
    
    # Stripe integration
    stripe_price_id_monthly = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Price ID for monthly subscription",
    )
    
    stripe_price_id_one_time = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Price ID for one-time payment",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('subtitle'),
            FieldPanel('title'),
            FieldPanel('description'),
        ], heading="Plan Information"),
        MultiFieldPanel([
            FieldPanel('price_old'),
            FieldPanel('price_period'),
            FieldPanel('price_new'),
            FieldPanel('discount_amount'),
        ], heading="Pricing"),
        MultiFieldPanel([
            FieldPanel('button_text'),
            FieldPanel('button_url'),
        ], heading="Call to Action"),
        MultiFieldPanel([
            FieldPanel('stripe_price_id_monthly'),
            FieldPanel('stripe_price_id_one_time'),
        ], heading="Stripe Integration"),
        MultiFieldPanel([
            FieldPanel('is_featured'),
            FieldPanel('order'),
            FieldPanel('is_active'),
        ], heading="Display Settings"),
        InlinePanel('features', label="Plan Features"),
    ]
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"
    
    def __str__(self):
        return f"{self.title} - ${self.price_new}"


class PlanFeature(Orderable):
    """
    Individual features/benefits included in a pricing plan.
    Each feature can be marked as included or not included (grayed out).
    """
    
    ICON_CHOICES = [
        ("pricing_icons/check.svg", "Check Mark"),
        ("pricing_icons/book.svg", "Book"),
        ("pricing_icons/shield.svg", "Shield"),
        ("pricing_icons/simulation.svg", "Simulation"),
    ]
    
    plan = ParentalKey(
        PricingPlan,
        on_delete=models.CASCADE,
        related_name="features",
        help_text="The pricing plan this feature belongs to",
    )
    
    text = models.CharField(
        max_length=255,
        help_text="Feature description (e.g., 'All 650 exam-like questions for your state')",
    )
    
    is_included = models.BooleanField(
        default=True,
        help_text="Whether this feature is included (unchecked = grayed out)",
    )
    
    icon_type = models.CharField(
        max_length=50,
        choices=ICON_CHOICES,
        default="pricing_icons/check.svg",
        help_text="Icon to display next to the feature",
    )
    
    icon = models.FileField(
        upload_to="plan_features/icons/",
        blank=True,
        null=True,
        help_text="Custom SVG icon (overrides icon_type if provided). Upload .svg files only.",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the plan",
    )
    
    # Additional details for expandable features
    detail_text = models.TextField(
        blank=True,
        help_text="Optional detailed description (shown on hover/click)",
    )
    
    panels = [
        FieldPanel('text'),
        FieldPanel('is_included'),
        FieldPanel('icon_type'),
        FieldPanel('icon'),
        FieldPanel('detail_text'),
    ]
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"
    
    def get_icon_url(self):
        """
        Return the icon URL, prioritizing custom uploaded icon over icon_type.
        """
        if self.icon:
            return self.icon.url
        return f"/static/{self.icon_type}"
    
    def __str__(self):
        status = "✓" if self.is_included else "✗"
        return f"{status} {self.plan.title}: {self.text[:50]}"


class ClientReview(models.Model):
    """
    Client testimonial/review model.
    Stores customer reviews with avatar, name, job title, rating, and review text.
    """
    avatar = models.ImageField(
        upload_to="reviews/avatars/",
        help_text="Client avatar/profile image (minimum dimensions: 112x112 pixels)",
    )
    
    image = models.ImageField(
        upload_to="reviews/images/",
        blank=True,
        null=True,
        help_text="Client review image (minimum dimensions: 800x600 pixels)",
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Client name (e.g., 'Bimosaurus')",
    )
    
    job_title = models.CharField(
        max_length=100,
        help_text="Client job title (e.g., 'Graphic Designer')",
    )
    
    rating = models.PositiveSmallIntegerField(
        default=5,
        help_text="Rating out of 5 stars (1-5)",
        choices=[(i, f"{i} Stars") for i in range(1, 6)],
    )
    
    review_text = models.TextField(
        help_text="The review/testimonial text",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this review is displayed on the site",
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "Client Review"
        verbose_name_plural = "Client Reviews"
    
    def clean(self):
        """
        Validate avatar dimensions (minimum 112x112 pixels) and image dimensions (minimum 800x600 pixels).
        """
        super().clean()
        
        errors = {}
        
        # Validate avatar dimensions
        if self.avatar:
            try:
                img = Image.open(self.avatar)
                width, height = img.size
                
                if width < 112 or height < 112:
                    errors['avatar'] = f'Avatar dimensions must be at least 112x112 pixels. Current dimensions: {width}x{height} pixels.'
            except Exception as e:
                if not isinstance(e, ValidationError):
                    errors['avatar'] = 'Unable to validate avatar. Please ensure it is a valid image file.'
        
        # Validate review image dimensions
        if self.image:
            try:
                img = Image.open(self.image)
                width, height = img.size
                
                if width < 800 or height < 600:
                    errors['image'] = f'Image dimensions must be at least 800x600 pixels. Current dimensions: {width}x{height} pixels.'
            except Exception as e:
                if not isinstance(e, ValidationError):
                    errors['image'] = 'Unable to validate image. Please ensure it is a valid image file.'
        
        if errors:
            raise ValidationError(errors)
    
    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class ContactInfo(models.Model):
    """
    Contact information model for the Contact Us page.
    Stores business contact details like address, phone numbers, and emails.
    Only one instance should exist (singleton pattern).
    """
    address_line1 = models.CharField(
        max_length=255,
        help_text="First line of address (e.g., street address in Armenian)",
    )
    
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Second line of address (e.g., translated address)",
    )
    
    phone_primary = models.CharField(
        max_length=20,
        help_text="Primary phone number (e.g., 011 580606)",
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        help_text="Secondary phone number (e.g., 044 580606)",
    )
    
    email_primary = models.EmailField(
        help_text="Primary email address (e.g., info@smv.am)",
    )
    
    email_secondary = models.EmailField(
        blank=True,
        help_text="Secondary email address (e.g., nn@consultant.com)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Only one ContactInfo should be active at a time",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"
    
    def __str__(self):
        return f"Contact Info - {self.email_primary}"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one ContactInfo is active at a time (singleton pattern).
        """
        if self.is_active:
            ContactInfo.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Contact(models.Model):
    """
    Contact form submission model.
    Stores messages from users who contact the site.
    """
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Contact person's name",
    )
    
    email = models.EmailField(
        help_text="Contact person's email address",
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Contact person's phone number",
    )
    
    message = models.TextField(
        help_text="The message content",
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        help_text="Status of the contact request",
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
    
    def __str__(self):
        return f"{self.name} - {self.email}"


class Partner(models.Model):
    """
    Partner/sponsor model for displaying partner logos and information.
    Stores partner details like logo and description.
    """
    logo = models.ImageField(
        upload_to="partners/logos/",
        help_text="Partner logo image",
    )
    
    description = models.TextField(
        help_text="Partner description (e.g., 'Great potential for cooperation with Ineco Bank for over 10 years')",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this partner is displayed on the site",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
    
    def __str__(self):
        return f"Partner #{self.id}"


class MainBanner(models.Model):
    """
    Main banner content model.
    Stores the main hero section content with image, title, and description.
    Only one instance should be active at a time (singleton pattern).
    """
    image = models.ImageField(
        upload_to="main_banner/images/",
        help_text="Main banner hero image (minimum dimensions: 1108x1206 pixels)",
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Main title for the main banner hero section",
    )
    
    title2 = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Secondary title for the main banner hero section",
    )
    
    description = models.TextField(
        help_text="Description text for the main banner hero section",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this main banner content is active",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Main Banner"
        verbose_name_plural = "Main Banners"
    
    def __str__(self):
        return f"{self.title[:50]}"
    
    def clean(self):
        """
        Validate image dimensions (minimum 1108x1206 pixels).
        """
        super().clean()
        
        if self.image:
            try:
                img = Image.open(self.image)
                width, height = img.size
                
                if width < 1108 or height < 1206:
                    raise ValidationError({
                        'image': f'Image dimensions must be at least 1108x1206 pixels. '
                                f'Current dimensions: {width}x{height} pixels.'
                    })
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                raise ValidationError({
                    'image': 'Unable to validate image. Please ensure it is a valid image file.'
                })
    
    def save(self, *args, **kwargs):
        """
        Ensure only one MainBanner is active at a time (singleton pattern).
        """
        if self.is_active:
            MainBanner.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
