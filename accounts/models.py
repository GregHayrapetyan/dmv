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
    AUTH_PROVIDER_CHOICES = (
        ('email', 'Email'),
        ('google', 'Google'),
        ('apple', 'Apple'),
    )

    username = None  # Remove username field from AbstractUser
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        validators=[RegexValidator(r"^[+0-9()\-\s]{7,20}$", "Invalid phone format")],
    )
    is_email_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    auth_provider = models.CharField(
        max_length=10, choices=AUTH_PROVIDER_CHOICES, default='email',
        help_text="How the user originally registered"
    )
    apple_sub = models.CharField(
        max_length=255, unique=True, null=True, blank=True,
        help_text="Apple's stable user identifier (sub claim) for Sign in with Apple"
    )

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


class PaymentMethod(models.Model):
    """Stores payment method details locally (synced from Stripe)."""
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    stripe_payment_method_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Stripe PaymentMethod ID (e.g. pm_xxx)"
    )
    card_brand = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Card brand (visa, mastercard, amex, etc.)"
    )
    card_last4 = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        help_text="Last 4 digits of card number"
    )
    card_exp_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Card expiration month (1-12)"
    )
    card_exp_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Card expiration year"
    )
    billing_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Cardholder / billing name"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default payment method"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['stripe_payment_method_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.card_brand} ****{self.card_last4}"


class Subscription(models.Model):
    """User subscription model for managing Stripe recurring subscriptions."""
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
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
        help_text="Stripe subscription ID"
    )
    stripe_price_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Stripe recurring Price ID"
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
        help_text="Billing interval in days (7/30/90)"
    )
    is_one_time_purchase = models.BooleanField(
        default=False,
        help_text="Deprecated - always False for recurring subscriptions"
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
            if self.current_period_end > timezone.now():
                return True
            else:
                # Auto-expire on access check
                self.status = 'expired'
                self.save(update_fields=['status', 'updated_at'])
                return False
        
        # Active subscription without period_end yet (set via webhook)
        return True
    
    def get_plan_display_name(self):
        """Get friendly display name for the plan."""
        tier_info = {
            'starter': ('Starter', '$9.99', '7 days'),
            'standard': ('Standard', '$19.99', '30 days'),
            'premium': ('Premium', '$29.99', '90 days'),
        }
        info = tier_info.get(self.plan_tier)
        if info:
            return f'{info[0]} {info[1]} / {info[2]}'
        return 'Unknown Plan'
    
    def days_remaining(self):
        """Calculate days remaining in current billing period."""
        if not self.current_period_end:
            return 0
        
        remaining = self.current_period_end - timezone.now()
        return max(0, remaining.days)
