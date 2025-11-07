from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import secrets
from .models import EmailOTP

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    repeat_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "phone", "email", "password", "repeat_password")

    def validate(self, attrs):
        if attrs["password"] != attrs["repeat_password"]:
            raise serializers.ValidationError({"repeat_password": "Passwords do not match"})
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
        send_mail(
            "Verify your email",
            f"Your verification code is: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(code)
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
            raise serializers.ValidationError("User not found")
        try:
            otp = EmailOTP.objects.filter(user=user, purpose="verify_email").latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("No verification code found")
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
            raise serializers.ValidationError("Email not found")
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        code = f"{secrets.randbelow(10**6):06d}"
        print(code)
        EmailOTP.objects.create(
            user=user,
            code=code,
            purpose="reset_password",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        send_mail("Reset password", f"Code: {code}", settings.DEFAULT_FROM_EMAIL, [user.email])


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        try:
            otp = EmailOTP.objects.filter(user=user, purpose="reset_password").latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("No reset code found")
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