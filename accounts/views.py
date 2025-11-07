from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    LoginSerializer, RegisterSerializer, ConfirmEmailSerializer, RequestPasswordResetSerializer,
    ResetPasswordSerializer, GoogleLoginSerializer,

)
from django.conf import settings

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        tokens = RefreshToken.for_user(user)
        return Response({
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        })

class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "Reset code sent"})

class ConfirmEmailView(generics.GenericAPIView):
    serializer_class = ConfirmEmailSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "Email confirmed"})

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "Password updated"})

class GoogleLoginView(generics.GenericAPIView):
    serializer_class = GoogleLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Accepts a Google id_token and returns app JWTs. Verifies token locally.
        On real deployment, also check aud == GOOGLE_OAUTH_CLIENT_ID.
        """
        from google.oauth2 import id_token
        from google.auth.transport import requests as grequests

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["id_token"]
        info = id_token.verify_oauth2_token(token, grequests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID or None)
        email = info.get("email")
        first = info.get("given_name", "")
        last = info.get("family_name", "")
        user, _ = User.objects.get_or_create(email=email, defaults={"first_name": first, "last_name": last, "username": email})
        tokens = RefreshToken.for_user(user)
        return Response({"access": str(tokens.access_token), "refresh": str(tokens)})