from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema_field
import secrets
import logging
from .models import EmailOTP, Subscription

logger = logging.getLogger(__name__)

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    repeat_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password", "repeat_password")

    def validate(self, attrs):
        if attrs["password"] != attrs["repeat_password"]:
            raise serializers.ValidationError({"repeat_password": "Passwords do not match"})
        
        # Check if email already exists and is verified
        email = attrs.get("email")
        if email and User.objects.filter(email=email, is_email_verified=True).exists():
            raise serializers.ValidationError({"email": "This email is already registered and verified."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeat_password")
        user = User.objects.create_user(**validated_data)
        # Send verify email code
        code = f"{secrets.randbelow(10**6):06d}"
        EmailOTP.objects.create(
            user=user,
            code=code,
            purpose="verify_email",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        try:
            send_mail(
                "Verify your email",
                f"Your verification code is: {code}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            raise serializers.ValidationError("Failed to send verification email. Please try again.")
        return user

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email or phone")
    password = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        password = attrs["password"]
        User = get_user_model()

        user = None
        # email (case-insensitive) vs phone
        if "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                user = None
        else:
            try:
                user = User.objects.get(phone=identifier)
            except User.DoesNotExist:
                user = None

        # check password explicitly without Django auth backend magic
        if not user or not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": ["Invalid credentials"]})

        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["User is inactive"]})

        attrs["user"] = user
        return attrs


class ConfirmEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or code")
        try:
            otp = EmailOTP.objects.filter(user=user, purpose="verify_email").latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid email or code")
        if otp.code != attrs["code"] or not otp.is_valid():
            raise serializers.ValidationError("Invalid or expired code")
        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        otp = self.validated_data["otp"]
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return user

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            raise serializers.ValidationError("If this email exists, a reset code will be sent.")
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        code = f"{secrets.randbelow(10**6):06d}"
        EmailOTP.objects.create(
            user=user,
            code=code,
            purpose="reset_password",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        try:
            send_mail(
                "Reset password",
                f"Your password reset code is: {code}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            raise serializers.ValidationError("Failed to send reset email. Please try again.")


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or code")
        try:
            otp = EmailOTP.objects.filter(user=user, purpose="reset_password").latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid email or code")
        if otp.code != attrs["code"] or not otp.is_valid():
            raise serializers.ValidationError("Invalid or expired code")
        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        otp = self.validated_data["otp"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return user

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (excludes avatar)."""
    
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone")


class UserSerializer(serializers.ModelSerializer):
    has_active_subscription = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "phone", "is_email_verified", "date_joined", "has_active_subscription", "avatar", "state")
        read_only_fields = ("id", "email", "is_email_verified", "date_joined")
    
    @extend_schema_field(serializers.BooleanField())
    def get_has_active_subscription(self, obj):
        """Check if user has an active subscription."""
        try:
            return obj.subscription.has_access()
        except Subscription.DoesNotExist:
            return False
    
    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_avatar(self, obj):
        """Return avatar URL if exists."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_state(self, obj):
        """Return user's state from profile if exists."""
        try:
            if obj.profile and obj.profile.state:
                return obj.profile.state.name
            return None
        except Exception:
            return None


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription information."""
    
    class Meta:
        model = Subscription
        fields = (
            'id', 'status', 'current_period_start', 'current_period_end',
            'cancel_at_period_end', 'created_at', 'updated_at'
        )
        read_only_fields = fields


class SetAvatarSerializer(serializers.Serializer):
    """Serializer for setting user avatar."""
    
    @extend_schema_field({"type": "string", "format": "binary"})
    class AvatarField(serializers.ImageField):
        pass
    
    avatar = AvatarField(
        required=True,
        help_text="Upload an image file (JPEG, PNG, GIF, or WebP, max 5MB)"
    )
    
    def validate_avatar(self, value):
        """Validate avatar file size and type."""
        # Max file size: 5MB
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Avatar file size cannot exceed 5MB.")
        
        # Allowed file types
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Avatar must be a JPEG, PNG, GIF, or WebP image.")
        
        return value