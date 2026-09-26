from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema_field
import secrets
import logging
from .models import EmailOTP, Subscription, PaymentMethod
from .email_utils import send_verification_email, send_password_reset_email
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
        # Send email asynchronously to avoid blocking the request
        send_verification_email(user.email, code)
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

        # Check if email is verified
        if not user.is_email_verified:
            raise serializers.ValidationError({"non_field_errors": ["Please verify your email before logging in"]})

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
        # Send email asynchronously to avoid blocking the request
        send_password_reset_email(user.email, code)
        
        # Return the code so it can be included in the response
        return code


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
    id_token = serializers.CharField(required=False, allow_blank=True, help_text="Google ID token (JWT)")
    access_token = serializers.CharField(required=False, allow_blank=True, help_text="Google access token")
    
    def validate(self, attrs):
        if not attrs.get('id_token') and not attrs.get('access_token'):
            raise serializers.ValidationError("Either id_token or access_token must be provided")
        return attrs

class AppleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True, help_text="Apple ID token (JWT)")
    user_data = serializers.JSONField(required=False, allow_null=True, help_text="User data (only provided on first login)")
    
    def validate(self, attrs):
        if not attrs.get('id_token'):
            raise serializers.ValidationError("id_token is required")
        return attrs

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (excludes avatar)."""
    state = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    age = serializers.IntegerField(required=False, allow_null=True, write_only=True, min_value=0)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', 'prefer_not_to_say'],
        required=False,
        allow_null=True,
        write_only=True
    )
    vehicle = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "state", "age", "gender", "vehicle")
    
    def update(self, instance, validated_data):
        # Extract profile-related fields
        state_id = validated_data.pop('state', None)
        age = validated_data.pop('age', None)
        gender = validated_data.pop('gender', None)
        vehicle_id = validated_data.pop('vehicle', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create profile
        from onboarding.models import Profile, State, Vehicle
        profile, _ = Profile.objects.get_or_create(user=instance)
        
        if state_id is not None:
            if state_id:
                try:
                    profile.state = State.objects.get(id=state_id)
                except State.DoesNotExist:
                    pass
            else:
                profile.state = None
        
        if age is not None:
            profile.age = age
        
        if gender is not None:
            profile.gender = gender
        
        if vehicle_id is not None:
            if vehicle_id:
                try:
                    profile.vehicle = Vehicle.objects.get(id=vehicle_id)
                except Vehicle.DoesNotExist:
                    pass
            else:
                profile.vehicle = None
        
        profile.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    has_active_subscription = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "phone", "is_email_verified", "date_joined", "has_active_subscription", "avatar", "state", "age", "gender", "vehicle", "auth_provider")
        read_only_fields = ("id", "email", "is_email_verified", "date_joined", "auth_provider")
    
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
    
    @extend_schema_field(serializers.DictField(allow_null=True, required=False))
    def get_state(self, obj):
        """Return user's state from profile if exists."""
        try:
            if obj.profile and obj.profile.state:
                return {
                    "id": obj.profile.state.id,
                    "name": obj.profile.state.name
                }
            return None
        except Exception:
            return None
    
    @extend_schema_field(serializers.IntegerField(allow_null=True, required=False))
    def get_age(self, obj):
        """Return user's age from profile if exists."""
        try:
            if obj.profile:
                return obj.profile.age
            return None
        except Exception:
            return None
    
    @extend_schema_field(serializers.CharField(allow_null=True, required=False))
    def get_gender(self, obj):
        """Return user's gender from profile if exists."""
        try:
            if obj.profile:
                return obj.profile.gender
            return None
        except Exception:
            return None
    
    @extend_schema_field(serializers.DictField(allow_null=True, required=False))
    def get_vehicle(self, obj):
        """Return user's vehicle from profile if exists."""
        try:
            if obj.profile and obj.profile.vehicle:
                request = self.context.get('request')
                vehicle_data = {
                    "id": obj.profile.vehicle.id,
                    "name": obj.profile.vehicle.name
                }
                if obj.profile.vehicle.image:
                    if request:
                        vehicle_data["image"] = request.build_absolute_uri(obj.profile.vehicle.image.url)
                    else:
                        vehicle_data["image"] = obj.profile.vehicle.image.url
                    if obj.profile.vehicle.image_width:
                        vehicle_data["image_width"] = obj.profile.vehicle.image_width
                    if obj.profile.vehicle.image_height:
                        vehicle_data["image_height"] = obj.profile.vehicle.image_height
                else:
                    vehicle_data["image"] = None
                return vehicle_data
            return None
        except Exception:
            return None


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription information."""
    plan_display_name = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    next_payment_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = (
            'id', 'status', 'payment_provider', 'plan_tier', 'access_duration_days',
            'current_period_start', 'current_period_end', 'cancel_at_period_end',
            'plan_display_name', 'days_remaining', 'next_payment_date',
            'created_at', 'updated_at'
        )
        read_only_fields = fields
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_plan_display_name(self, obj):
        """Get friendly plan name."""
        return obj.get_plan_display_name() if obj.plan_tier else None
    
    @extend_schema_field(serializers.IntegerField())
    def get_days_remaining(self, obj):
        """Get days remaining in current billing period."""
        return obj.days_remaining()
    
    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_next_payment_date(self, obj):
        """Get next payment date (current_period_end for recurring)."""
        if obj.cancel_at_period_end:
            return None
        return obj.current_period_end


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment method information."""
    
    class Meta:
        model = PaymentMethod
        fields = (
            'id', 'stripe_payment_method_id', 'card_brand', 'card_last4',
            'card_exp_month', 'card_exp_year', 'billing_name', 'is_default',
            'created_at', 'updated_at'
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


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    old_password = serializers.CharField(required=False, write_only=True, allow_null=True, allow_blank=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def _is_social_auth_user(self):
        """Check if the user registered via Google or Apple."""
        user = self.context['request'].user
        return user.auth_provider in ('google', 'apple')
    
    def validate(self, attrs):
        """Validate that new passwords match and old password is correct."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
        
        if not self._is_social_auth_user():
            if 'old_password' not in attrs or not attrs['old_password']:
                raise serializers.ValidationError({"old_password": "Old password is required"})
            if attrs['old_password'] == attrs['new_password']:
                raise serializers.ValidationError({"new_password": "New password must be different from old password"})
        
        return attrs
    
    def validate_old_password(self, value):
        """Validate that the old password is correct."""
        if self._is_social_auth_user():
            return value
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value