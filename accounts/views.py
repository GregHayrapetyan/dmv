from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    LoginSerializer, RegisterSerializer, ConfirmEmailSerializer, RequestPasswordResetSerializer,
    ResetPasswordSerializer, GoogleLoginSerializer,
)
from .throttling import OTPRateThrottle
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Registration successful. Please check your email for verification code."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        tokens = RefreshToken.for_user(user)
        logger.info(f"User logged in: {user.email}")
        return Response({
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        })

class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "If this email exists, a reset code has been sent."})

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
        from google.auth.exceptions import GoogleAuthError

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["id_token"]
        
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            logger.error("Google OAuth Client ID not configured")
            return Response(
                {"detail": "Google authentication is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            info = id_token.verify_oauth2_token(
                token, 
                grequests.Request(), 
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            email = info.get("email")
            if not email:
                return Response(
                    {"detail": "Email not provided by Google."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            first = info.get("given_name", "")
            last = info.get("family_name", "")
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "is_email_verified": True  # Google emails are pre-verified
                }
            )
            if created:
                logger.info(f"New user created via Google OAuth: {email}")
            
            tokens = RefreshToken.for_user(user)
            return Response({
                "access": str(tokens.access_token),
                "refresh": str(tokens)
            })
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {str(e)}")
            return Response(
                {"detail": "Invalid Google token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Unexpected error in Google login: {str(e)}")
            return Response(
                {"detail": "An error occurred during authentication."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )