# site_details/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from PIL import Image
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


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
    
    # Multilingual fields - Russian
    subtitle_ru = models.CharField(max_length=100, blank=True, verbose_name="Subtitle (Russian)")
    title_ru = models.CharField(max_length=100, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    price_period_ru = models.CharField(max_length=50, blank=True, verbose_name="Price Period (Russian)")
    button_text_ru = models.CharField(max_length=50, blank=True, verbose_name="Button Text (Russian)")
    
    # Multilingual fields - Armenian
    subtitle_hy = models.CharField(max_length=100, blank=True, verbose_name="Subtitle (Armenian)")
    title_hy = models.CharField(max_length=100, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    price_period_hy = models.CharField(max_length=50, blank=True, verbose_name="Price Period (Armenian)")
    button_text_hy = models.CharField(max_length=50, blank=True, verbose_name="Button Text (Armenian)")
    
    # Multilingual fields - Hindi
    subtitle_hi = models.CharField(max_length=100, blank=True, verbose_name="Subtitle (Hindi)")
    title_hi = models.CharField(max_length=100, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    price_period_hi = models.CharField(max_length=50, blank=True, verbose_name="Price Period (Hindi)")
    button_text_hi = models.CharField(max_length=50, blank=True, verbose_name="Button Text (Hindi)")
    
    # Multilingual fields - Spanish
    subtitle_es = models.CharField(max_length=100, blank=True, verbose_name="Subtitle (Spanish)")
    title_es = models.CharField(max_length=100, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    price_period_es = models.CharField(max_length=50, blank=True, verbose_name="Price Period (Spanish)")
    button_text_es = models.CharField(max_length=50, blank=True, verbose_name="Button Text (Spanish)")
    
    # Multilingual fields - Chinese
    subtitle_zh = models.CharField(max_length=100, blank=True, verbose_name="Subtitle (Chinese)")
    title_zh = models.CharField(max_length=100, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    price_period_zh = models.CharField(max_length=50, blank=True, verbose_name="Price Period (Chinese)")
    button_text_zh = models.CharField(max_length=50, blank=True, verbose_name="Button Text (Chinese)")
    
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
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"
    
    def __str__(self):
        return f"{self.title} - ${self.price_new}"


class PlanFeature(models.Model):
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
        validators=[FileExtensionValidator(allowed_extensions=['svg'])],
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
    
    # Multilingual fields - Russian
    text_ru = models.CharField(max_length=255, blank=True, verbose_name="Text (Russian)")
    detail_text_ru = models.TextField(blank=True, verbose_name="Detail Text (Russian)")
    
    # Multilingual fields - Armenian
    text_hy = models.CharField(max_length=255, blank=True, verbose_name="Text (Armenian)")
    detail_text_hy = models.TextField(blank=True, verbose_name="Detail Text (Armenian)")
    
    # Multilingual fields - Hindi
    text_hi = models.CharField(max_length=255, blank=True, verbose_name="Text (Hindi)")
    detail_text_hi = models.TextField(blank=True, verbose_name="Detail Text (Hindi)")
    
    # Multilingual fields - Spanish
    text_es = models.CharField(max_length=255, blank=True, verbose_name="Text (Spanish)")
    detail_text_es = models.TextField(blank=True, verbose_name="Detail Text (Spanish)")
    
    # Multilingual fields - Chinese
    text_zh = models.CharField(max_length=255, blank=True, verbose_name="Text (Chinese)")
    detail_text_zh = models.TextField(blank=True, verbose_name="Detail Text (Chinese)")
    
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
        help_text="Client avatar/profile image (exact dimensions: 300x300 pixels).",
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
    
    # Multilingual fields - Russian
    job_title_ru = models.CharField(max_length=100, blank=True, verbose_name="Job Title (Russian)")
    review_text_ru = models.TextField(blank=True, verbose_name="Review Text (Russian)")
    
    # Multilingual fields - Armenian
    job_title_hy = models.CharField(max_length=100, blank=True, verbose_name="Job Title (Armenian)")
    review_text_hy = models.TextField(blank=True, verbose_name="Review Text (Armenian)")
    
    # Multilingual fields - Hindi
    job_title_hi = models.CharField(max_length=100, blank=True, verbose_name="Job Title (Hindi)")
    review_text_hi = models.TextField(blank=True, verbose_name="Review Text (Hindi)")
    
    # Multilingual fields - Spanish
    job_title_es = models.CharField(max_length=100, blank=True, verbose_name="Job Title (Spanish)")
    review_text_es = models.TextField(blank=True, verbose_name="Review Text (Spanish)")
    
    # Multilingual fields - Chinese
    job_title_zh = models.CharField(max_length=100, blank=True, verbose_name="Job Title (Chinese)")
    review_text_zh = models.TextField(blank=True, verbose_name="Review Text (Chinese)")
    
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
        Validate avatar dimensions (exact 300x300 pixels) and image dimensions (minimum 800x600 pixels).
        """
        super().clean()
        
        errors = {}
        
        # Validate avatar dimensions
        if self.avatar:
            try:
                img = Image.open(self.avatar)
                width, height = img.size
                
                if width != 300 or height != 300:
                    errors['avatar'] = f'Avatar dimensions must be exactly 300x300 pixels. Current dimensions: {width}x{height} pixels.'
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
        blank=True,
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
    
    website_url = models.URLField(
        max_length=500,
        blank=True,
        default='',
        help_text="Partner's official website URL (e.g., 'https://www.partner.com')",
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
    
    # Statistics text fields
    stat_text1 = models.CharField(
        max_length=100,
        default="",
        help_text="First statistic text (e.g., '2200+ Success attempts')",
    )
    
    stat_text2 = models.CharField(
        max_length=100,
        default="",
        help_text="Second statistic text (e.g., '2350+ Success attempts')",
    )
    
    # Button fields
    button_name = models.CharField(
        max_length=100,
        default="",
        help_text="Button text (e.g., 'Video Guide')",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    title2_ru = models.CharField(max_length=200, blank=True, verbose_name="Secondary Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    stat_text1_ru = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 1 (Russian)")
    stat_text2_ru = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 2 (Russian)")
    button_name_ru = models.CharField(max_length=100, blank=True, verbose_name="Button Name (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    title2_hy = models.CharField(max_length=200, blank=True, verbose_name="Secondary Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    stat_text1_hy = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 1 (Armenian)")
    stat_text2_hy = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 2 (Armenian)")
    button_name_hy = models.CharField(max_length=100, blank=True, verbose_name="Button Name (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    title2_hi = models.CharField(max_length=200, blank=True, verbose_name="Secondary Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    stat_text1_hi = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 1 (Hindi)")
    stat_text2_hi = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 2 (Hindi)")
    button_name_hi = models.CharField(max_length=100, blank=True, verbose_name="Button Name (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    title2_es = models.CharField(max_length=200, blank=True, verbose_name="Secondary Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    stat_text1_es = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 1 (Spanish)")
    stat_text2_es = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 2 (Spanish)")
    button_name_es = models.CharField(max_length=100, blank=True, verbose_name="Button Name (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    title2_zh = models.CharField(max_length=200, blank=True, verbose_name="Secondary Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    stat_text1_zh = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 1 (Chinese)")
    stat_text2_zh = models.CharField(max_length=100, blank=True, verbose_name="Stat Text 2 (Chinese)")
    button_name_zh = models.CharField(max_length=100, blank=True, verbose_name="Button Name (Chinese)")
    
    button_link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Button URL or link (required if 'Use video as button link' is unchecked)",
    )
    
    # Video field
    video = models.FileField(
        upload_to="main_banner/videos/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['webm'])],
        help_text="Video file - webm only (required if 'Use video as button link' is checked)",
    )
    
    # Multilingual media - Russian
    image_ru = models.ImageField(upload_to="main_banner/images/", blank=True, null=True, verbose_name="Image (Russian)")
    video_ru = models.FileField(upload_to="main_banner/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm'])], verbose_name="Video (Russian)")
    
    # Multilingual media - Armenian
    image_hy = models.ImageField(upload_to="main_banner/images/", blank=True, null=True, verbose_name="Image (Armenian)")
    video_hy = models.FileField(upload_to="main_banner/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm'])], verbose_name="Video (Armenian)")
    
    # Multilingual media - Hindi
    image_hi = models.ImageField(upload_to="main_banner/images/", blank=True, null=True, verbose_name="Image (Hindi)")
    video_hi = models.FileField(upload_to="main_banner/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm'])], verbose_name="Video (Hindi)")
    
    # Multilingual media - Spanish
    image_es = models.ImageField(upload_to="main_banner/images/", blank=True, null=True, verbose_name="Image (Spanish)")
    video_es = models.FileField(upload_to="main_banner/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm'])], verbose_name="Video (Spanish)")
    
    # Multilingual media - Chinese
    image_zh = models.ImageField(upload_to="main_banner/images/", blank=True, null=True, verbose_name="Image (Chinese)")
    video_zh = models.FileField(upload_to="main_banner/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm'])], verbose_name="Video (Chinese)")
    
    use_video_as_button_link = models.BooleanField(
        default=False,
        help_text="Check to use video as button link (makes video required). Uncheck to use button link (makes button link required).",
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
        Validate that video is uploaded if use_video_as_button_link is checked.
        Validate that either button_link or video is provided (at least one required).
        """
        super().clean()
        
        errors = {}
        
        # Validate image dimensions
        if self.image:
            try:
                img = Image.open(self.image)
                width, height = img.size
                
                if width < 1108 or height < 1206:
                    errors['image'] = f'Image dimensions must be at least 1108x1206 pixels. ' \
                                     f'Current dimensions: {width}x{height} pixels.'
            except Exception as e:
                if not isinstance(e, ValidationError):
                    errors['image'] = 'Unable to validate image. Please ensure it is a valid image file.'
        
        # Validate based on use_video_as_button_link checkbox
        if self.use_video_as_button_link:
            # If checkbox is True, video is required
            if not self.video:
                errors['video'] = 'Video upload is required when "Use video as button link" is checked.'
        else:
            # If checkbox is False, button_link is required
            if not self.button_link:
                errors['button_link'] = 'Button link is required when "Use video as button link" is not checked.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Ensure only one MainBanner is active at a time (singleton pattern).
        """
        if self.is_active:
            MainBanner.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)


class HowItWorks(ClusterableModel):
    """
    How It Works section model.
    Stores the "How It Works" section content with background image, header, title, description,
    and individual steps explaining the process.
    Only one instance should be active at a time (singleton pattern).
    """
    # Background image
    background_image = models.ImageField(
        upload_to="how_it_works/backgrounds/",
        help_text="Background image for the How It Works section (e.g., cars in parking lot)",
    )
    
    # Section header
    section_header = models.CharField(
        max_length=100,
        default="HOW IT WORKS",
        help_text="Section header text (e.g., 'HOW IT WORKS')",
    )
    
    # Main title
    title = models.CharField(
        max_length=200,
        help_text="Main title (e.g., '4 simple steps to get road-ready')",
    )
    
    # Description
    description = models.TextField(
        help_text="Description text below the title (e.g., 'Remote assistants will work to ensure you can do your job well, regardless of where you are')",
    )
    
    # Multilingual fields - Russian
    section_header_ru = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Russian)")
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    section_header_hy = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Armenian)")
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    section_header_hi = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Hindi)")
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    section_header_es = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Spanish)")
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    section_header_zh = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Chinese)")
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this How It Works section is active",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "How It Works Section"
        verbose_name_plural = "How It Works Sections"
    
    def __str__(self):
        return f"{self.title[:50]}"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one HowItWorks is active at a time (singleton pattern).
        """
        if self.is_active:
            HowItWorks.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class HowItWorksStep(models.Model):
    """
    Individual step in the How It Works section.
    Each step has a number, title, and description.
    """
    how_it_works = ParentalKey(
        HowItWorks,
        on_delete=models.CASCADE,
        related_name="steps",
        help_text="The How It Works section this step belongs to",
    )
    
    step_number = models.CharField(
        max_length=10,
        help_text="Step number (e.g., '01', '02', '03', '04')",
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Step title (e.g., 'Sign up or start for free', 'Choose a test option')",
    )
    
    description = models.TextField(
        help_text="Step description (e.g., 'The world's largest and most liquid platform with spot, futures and options trading')",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    # Optional icon/image for the step
    icon = models.ImageField(
        upload_to="how_it_works/step_icons/",
        blank=True,
        null=True,
        help_text="Optional icon/image for this step",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    class Meta:
        ordering = ("order",)
        verbose_name = "How It Works Step"
        verbose_name_plural = "How It Works Steps"
    
    def __str__(self):
        return f"Step {self.step_number}: {self.title[:30]}"


class TrustSafety(ClusterableModel):
    """
    Trust & Safety section model.
    Stores the "Trust & Safety" section content with image, header, title,
    video button, registration button, and individual features.
    Only one instance should be active at a time (singleton pattern).
    """
    # Section header
    section_header = models.CharField(
        max_length=100,
        default="TRUST & SAFETY",
        help_text="Section header text (e.g., 'TRUST & SAFETY')",
    )
    
    # Main title
    title = models.CharField(
        max_length=200,
        help_text="Main title (e.g., 'It's fast and profitable with us')",
    )
    
    # Main image
    image = models.ImageField(
        upload_to="trust_safety/images/",
        help_text="Main image for the Trust & Safety section (minimum dimensions: 800x600 pixels)",
    )
    
    # Video file
    video = models.FileField(
        upload_to="trust_safety/videos/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])],
        help_text="Video file - webm or mp4 format",
    )
    
    # Multilingual media - Russian
    image_ru = models.ImageField(upload_to="trust_safety/images/", blank=True, null=True, verbose_name="Image (Russian)")
    video_ru = models.FileField(upload_to="trust_safety/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])], verbose_name="Video (Russian)")
    
    # Multilingual media - Armenian
    image_hy = models.ImageField(upload_to="trust_safety/images/", blank=True, null=True, verbose_name="Image (Armenian)")
    video_hy = models.FileField(upload_to="trust_safety/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])], verbose_name="Video (Armenian)")
    
    # Multilingual media - Hindi
    image_hi = models.ImageField(upload_to="trust_safety/images/", blank=True, null=True, verbose_name="Image (Hindi)")
    video_hi = models.FileField(upload_to="trust_safety/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])], verbose_name="Video (Hindi)")
    
    # Multilingual media - Spanish
    image_es = models.ImageField(upload_to="trust_safety/images/", blank=True, null=True, verbose_name="Image (Spanish)")
    video_es = models.FileField(upload_to="trust_safety/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])], verbose_name="Video (Spanish)")
    
    # Multilingual media - Chinese
    image_zh = models.ImageField(upload_to="trust_safety/images/", blank=True, null=True, verbose_name="Image (Chinese)")
    video_zh = models.FileField(upload_to="trust_safety/videos/", blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['webm', 'mp4'])], verbose_name="Video (Chinese)")
    
    # Button
    button_text = models.CharField(
        max_length=100,
        default="Start Registration",
        help_text="Button text (e.g., 'Start Registration')",
    )
    
    button_link = models.CharField(
        max_length=500,
        default="",
        help_text="Button URL or link",
    )
    
    # Multilingual fields - Russian
    section_header_ru = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Russian)")
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    button_text_ru = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Russian)")
    
    # Multilingual fields - Armenian
    section_header_hy = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Armenian)")
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    button_text_hy = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Armenian)")
    
    # Multilingual fields - Hindi
    section_header_hi = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Hindi)")
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    button_text_hi = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Hindi)")
    
    # Multilingual fields - Spanish
    section_header_es = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Spanish)")
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    button_text_es = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Spanish)")
    
    # Multilingual fields - Chinese
    section_header_zh = models.CharField(max_length=100, blank=True, verbose_name="Section Header (Chinese)")
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    button_text_zh = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Chinese)")
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this Trust & Safety section is active",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trust & Safety Section"
        verbose_name_plural = "Trust & Safety Sections"
    
    def __str__(self):
        return f"{self.title[:50]}"
    
    def clean(self):
        """
        Validate image dimensions (minimum 800x600 pixels).
        """
        super().clean()
        
        errors = {}
        
        # Validate image dimensions
        if self.image:
            try:
                img = Image.open(self.image)
                width, height = img.size
                
                if width < 800 or height < 600:
                    errors['image'] = f'Image dimensions must be at least 800x600 pixels. ' \
                                     f'Current dimensions: {width}x{height} pixels.'
            except Exception as e:
                if not isinstance(e, ValidationError):
                    errors['image'] = 'Unable to validate image. Please ensure it is a valid image file.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Ensure only one TrustSafety is active at a time (singleton pattern).
        """
        if self.is_active:
            TrustSafety.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)


class TrustSafetyFeature(models.Model):
    """
    Individual feature in the Trust & Safety section.
    Each feature has a number, title, and description.
    """
    trust_safety = ParentalKey(
        TrustSafety,
        on_delete=models.CASCADE,
        related_name="features",
        help_text="The Trust & Safety section this feature belongs to",
    )
    
    number = models.CharField(
        max_length=10,
        help_text="Feature number (e.g., '1', '2', '3')",
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Feature title (e.g., 'Updated questionnaire', 'From the official database')",
    )
    
    description = models.TextField(
        help_text="Feature description (e.g., 'Lorem ipsum dolor sit amet consectetur. Auctor')",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Trust & Safety Feature"
        verbose_name_plural = "Trust & Safety Features"
    
    def __str__(self):
        return f"Feature {self.number}: {self.title[:30]}"


class SuccessSteps(ClusterableModel):
    """
    Success Steps section model.
    Stores the "Reach your success in three steps" section content with title, description,
    button, and individual steps explaining the process.
    Only one instance should be active at a time (singleton pattern).
    """
    # Main title
    title = models.CharField(
        max_length=200,
        default="Reach your success in three steps.",
        help_text="Main title (e.g., 'Reach your success in three steps.')",
    )
    
    # Description
    description = models.TextField(
        help_text="Description text below the title (e.g., 'Lorem ipsum dolor sit amet, consectetur adipiscing elit...')",
    )
    
    # Button
    button_text = models.CharField(
        max_length=100,
        default="DEMO TEST",
        help_text="Button text (e.g., 'DEMO TEST')",
    )
    
    button_link = models.CharField(
        max_length=500,
        default="",
        help_text="Button URL or link",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    button_text_ru = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    button_text_hy = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    button_text_hi = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    button_text_es = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    button_text_zh = models.CharField(max_length=100, blank=True, verbose_name="Button Text (Chinese)")
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this Success Steps section is active",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Success Steps Section"
        verbose_name_plural = "Success Steps Sections"
    
    def __str__(self):
        return f"{self.title[:50]}"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one SuccessSteps is active at a time (singleton pattern).
        """
        if self.is_active:
            SuccessSteps.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class SuccessStep(models.Model):
    """
    Individual step in the Success Steps section.
    Each step has an icon, title, and description.
    """
    success_steps = ParentalKey(
        SuccessSteps,
        on_delete=models.CASCADE,
        related_name="steps",
        help_text="The Success Steps section this step belongs to",
    )
    
    icon = models.ImageField(
        upload_to="success_steps/icons/",
        help_text="Icon/image for this step (e.g., sign up icon, practice icon, exam icon)",
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Step title (e.g., 'Sign Up in Seconds', 'Practice All Tests', 'Pass Your Exam')",
    )
    
    description = models.TextField(
        help_text="Step description (e.g., 'Enter your name, email and password.')",
    )
    
    link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Link/path for this step (e.g., '/signup', 'https://example.com')",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Success Step"
        verbose_name_plural = "Success Steps"
    
    def __str__(self):
        return f"{self.title[:30]}"


class LearningOptions(ClusterableModel):
    """
    Learning Options section model.
    Stores the "Reach your success in three steps" section content with title, description,
    and individual learning option cards.
    Only one instance should be active at a time (singleton pattern).
    """
    # Main title
    title = models.CharField(
        max_length=200,
        default="Reach your success in three steps.",
        help_text="Main title (e.g., 'Reach your success in three steps.')",
    )
    
    # Description
    description = models.TextField(
        help_text="Description text below the title",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this Learning Options section is active",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Learning Options Section"
        verbose_name_plural = "Learning Options Sections"
    
    def __str__(self):
        return f"{self.title[:50]}"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one LearningOptions is active at a time (singleton pattern).
        """
        if self.is_active:
            LearningOptions.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class LearningOption(models.Model):
    """
    Individual option card in the Learning Options section.
    Each option has an image, title, and description.
    """
    learning_options = ParentalKey(
        LearningOptions,
        on_delete=models.CASCADE,
        related_name="options",
        help_text="The Learning Options section this option belongs to",
    )
    
    image = models.ImageField(
        upload_to="learning_options/images/",
        help_text="Image for this option card",
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Option title (e.g., 'Start Test', 'Practice Test', 'Real Exam Simul.', 'By Topic')",
    )
    
    description = models.TextField(
        help_text="Option description (e.g., '650+ exam-like questions', 'Road Signs, Rules, Fines')",
    )
    
    link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Optional URL or route for this option card",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=200, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=200, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=200, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=200, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=200, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    class Meta:
        ordering = ("order",)
        verbose_name = "Learning Option"
        verbose_name_plural = "Learning Options"
    
    def __str__(self):
        return f"{self.title[:30]}"


class SocialNetwork(models.Model):
    """
    Social network link model.
    Stores social media platform details like name, icon, and URL.
    The 'hide' field controls whether the link is visible on the frontend.
    """
    name = models.CharField(
        max_length=100,
        help_text="Social network name (e.g., 'Facebook', 'Instagram', 'Twitter')",
    )
    
    icon = models.FileField(
        upload_to="social_networks/icons/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['svg', 'png', 'jpg', 'jpeg', 'webp'])],
        help_text="Social network icon (SVG, PNG, JPG, or WebP)",
    )
    
    url = models.URLField(
        max_length=500,
        help_text="Social network profile URL (e.g., 'https://facebook.com/yourpage')",
    )
    
    hide = models.BooleanField(
        default=False,
        help_text="Hide this social network link from the frontend",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this social network is available on the site",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "Social Network"
        verbose_name_plural = "Social Networks"
    
    def __str__(self):
        return self.name


class FooterColumn(ClusterableModel):
    """
    Footer navigation column model.
    Represents a column in the site footer (e.g., 'Navigation', 'Work Process').
    Each column contains a set of footer links managed inline.
    The 'hide' field controls whether the column is visible on the frontend.
    """
    title = models.CharField(
        max_length=100,
        help_text="Column title (e.g., 'Navigation', 'Work Process')",
    )
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=100, blank=True, verbose_name="Title (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=100, blank=True, verbose_name="Title (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=100, blank=True, verbose_name="Title (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=100, blank=True, verbose_name="Title (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=100, blank=True, verbose_name="Title (Chinese)")
    
    hide = models.BooleanField(
        default=False,
        help_text="Hide this column from the frontend",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this footer column is available on the site",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "Footer Column"
        verbose_name_plural = "Footer Columns"
    
    def __str__(self):
        return self.title


class FooterLink(models.Model):
    """
    Individual link in a footer column.
    Each link has a label, URL, and display order.
    The 'hide' field controls whether the link is visible on the frontend.
    """
    column = ParentalKey(
        FooterColumn,
        on_delete=models.CASCADE,
        related_name="links",
        help_text="The footer column this link belongs to",
    )
    
    label = models.CharField(
        max_length=200,
        help_text="Link label (e.g., 'Home', 'About Us', 'Premium')",
    )
    
    # Multilingual fields - Russian
    label_ru = models.CharField(max_length=200, blank=True, verbose_name="Label (Russian)")
    
    # Multilingual fields - Armenian
    label_hy = models.CharField(max_length=200, blank=True, verbose_name="Label (Armenian)")
    
    # Multilingual fields - Hindi
    label_hi = models.CharField(max_length=200, blank=True, verbose_name="Label (Hindi)")
    
    # Multilingual fields - Spanish
    label_es = models.CharField(max_length=200, blank=True, verbose_name="Label (Spanish)")
    
    # Multilingual fields - Chinese
    label_zh = models.CharField(max_length=200, blank=True, verbose_name="Label (Chinese)")
    
    url = models.CharField(
        max_length=500,
        help_text="Link URL - can be a relative path (e.g., '/about') or a full URL (e.g., 'https://example.com')",
    )
    
    hide = models.BooleanField(
        default=False,
        help_text="Hide this link from the frontend",
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this footer link is available on the site",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "Footer Link"
        verbose_name_plural = "Footer Links"
    
    def __str__(self):
        return f"{self.label} ({self.url})"
