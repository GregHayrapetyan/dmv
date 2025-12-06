from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

class User(AbstractUser):
    username = None  # Remove username field from AbstractUser
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        validators=[RegexValidator(r"^[+0-9()\-\s]{7,20}$", "Invalid phone format")],
    )
    is_email_verified = models.BooleanField(default=False)

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
