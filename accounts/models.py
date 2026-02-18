from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # Remove username field from AbstractUser
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        validators=[RegexValidator(r"^[+0-9()\-\s]{7,20}$", "Invalid phone format")],
    )
    is_email_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email is already the USERNAME_FIELD, so it shouldn't be in REQUIRED_FIELDS


class EmailOTP(models.Model):
    PURPOSE_CHOICES = (
        ("verify_email", "Verify Email"),
        ("reset_password", "Reset Password"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_codes")
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (not self.is_used) and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"


class Subscription(models.Model):
    """User subscription model for managing Stripe subscriptions and one-time access purchases."""
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('unpaid', 'Unpaid'),
    )
    
    PLAN_TIER_CHOICES = (
        ('starter', 'Starter - 7 Days'),
        ('standard', 'Standard - 30 Days'),
        ('premium', 'Premium - 90 Days'),
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Stripe customer ID"
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Stripe subscription ID (for recurring) or Payment Intent ID (for one-time)"
    )
    stripe_price_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Stripe Price ID that user purchased"
    )
    plan_tier = models.CharField(
        max_length=20,
        choices=PLAN_TIER_CHOICES,
        null=True,
        blank=True,
        help_text="Plan tier (starter/standard/premium)"
    )
    access_duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of days of access (7/30/90)"
    )
    is_one_time_purchase = models.BooleanField(
        default=False,
        help_text="True for one-time purchase, False for recurring subscription"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='incomplete'
    )
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['stripe_customer_id']),
            models.Index(fields=['stripe_subscription_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.status}"
    
    def is_active(self):
        """Check if subscription is active or trialing."""
        return self.status in ['active', 'trialing']
    
    def has_access(self):
        """Check if user has access to premium content."""
        if not self.is_active():
            return False
        
        if self.current_period_end:
            return self.current_period_end > timezone.now()
        
        return False
    
    def get_plan_display_name(self):
        """Get friendly display name for the plan."""
        if self.plan_tier == 'starter':
            return 'Starter - 7 Days Access'
        elif self.plan_tier == 'standard':
            return 'Standard - 30 Days Access'
        elif self.plan_tier == 'premium':
            return 'Premium - 90 Days Access'
        return 'Unknown Plan'
    
    def days_remaining(self):
        """Calculate days remaining in access period."""
        if not self.current_period_end:
            return 0
        
        remaining = self.current_period_end - timezone.now()
        return max(0, remaining.days)
