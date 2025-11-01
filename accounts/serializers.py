from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import secrets

User = get_user_model()

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