from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import (
    LoginSerializer, RegisterSerializer, ConfirmEmailSerializer, RequestPasswordResetSerializer,
    ResetPasswordSerializer, GoogleLoginSerializer, UserSerializer,
)
from .throttling import OTPRateThrottle
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Creates a new user and sends a verification code to their email.
    The user must verify their email before they can log in.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRateThrottle]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account and send email verification code. Rate limited to 5 requests per hour.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Registration successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Registration successful. Please check your email for verification code."},
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error (e.g., passwords don't match, email already exists)"),
            429: OpenApiResponse(description="Too many requests - rate limit exceeded"),
        },
        tags=["Authentication"],
    )
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
    """
    Authenticate user and return JWT tokens.
    
    Accepts email or phone number as identifier.
    Returns access and refresh tokens for authenticated requests.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Login user",
        description="Authenticate with email/phone and password. Returns JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid credentials or inactive user"),
        },
        tags=["Authentication"],
    )
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
    """
    Request a password reset code.
    
    Sends a 6-digit verification code to the user's email.
    Rate limited to prevent abuse.
    """
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRateThrottle]

    @extend_schema(
        summary="Request password reset",
        description="Send a password reset code to the user's email. Rate limited to 5 requests per hour.",
        request=RequestPasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                description="Reset code sent (or email doesn't exist - security measure)",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "If this email exists, a reset code has been sent."},
                    )
                ]
            ),
            429: OpenApiResponse(description="Too many requests - rate limit exceeded"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "If this email exists, a reset code has been sent."})

class ConfirmEmailView(generics.GenericAPIView):
    """
    Verify email address with OTP code.
    
    Confirms the user's email using the 6-digit code sent during registration.
    """
    serializer_class = ConfirmEmailSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Confirm email address",
        description="Verify email with the 6-digit code sent during registration. Code expires in 10 minutes.",
        request=ConfirmEmailSerializer,
        responses={
            200: OpenApiResponse(
                description="Email confirmed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Email confirmed"},
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid or expired code"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "Email confirmed"})

class ResetPasswordView(generics.GenericAPIView):
    """
    Reset password with verification code.
    
    Updates the user's password using the code sent via email.
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Reset password",
        description="Reset password using the verification code sent to email. Code expires in 10 minutes.",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Password updated"},
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid or expired code, or password validation failed"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"detail": "Password updated"})

class GoogleLoginView(generics.GenericAPIView):
    """
    Authenticate with Google OAuth.
    
    Accepts a Google ID token, verifies it, and creates/authenticates the user.
    Returns JWT tokens for the application.
    """
    serializer_class = GoogleLoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Google OAuth login",
        description="Authenticate using Google ID token. Creates new user if doesn't exist. Email is automatically verified.",
        request=GoogleLoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Authentication successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "user": {
                                "id": 1,
                                "email": "user@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "is_email_verified": True
                            }
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid token or email not verified by Google"),
            401: OpenApiResponse(description="Invalid or expired Google token"),
            503: OpenApiResponse(description="Google OAuth not configured on server"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """Accepts a Google id_token and returns app JWTs. Verifies token locally."""
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
            # Verify the token with Google
            info = id_token.verify_oauth2_token(
                token, 
                grequests.Request(), 
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
            
            # Validate required fields
            email = info.get("email")
            email_verified = info.get("email_verified", False)
            
            if not email:
                return Response(
                    {"detail": "Email not provided by Google."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if email is verified by Google
            if not email_verified:
                logger.warning(f"Unverified email attempted Google login: {email}")
                return Response(
                    {"detail": "Email not verified by Google."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract user information
            first_name = info.get("given_name", "")
            last_name = info.get("family_name", "")
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_email_verified": True  # Google emails are pre-verified
                }
            )
            
            # Update existing user's email verification status if not already verified
            if not created and not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                logger.info(f"Email verified via Google OAuth for existing user: {email}")
            
            if created:
                logger.info(f"New user created via Google OAuth: {email}")
            
            # Generate JWT tokens
            tokens = RefreshToken.for_user(user)
            return Response({
                "access": str(tokens.access_token),
                "refresh": str(tokens),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_email_verified": user.is_email_verified
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Token is expired or invalid format
            logger.error(f"Invalid token format: {str(e)}")
            return Response(
                {"detail": "Invalid or expired Google token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
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

class MeView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    
    Returns the authenticated user's profile information.
    Allows updating first_name, last_name, and phone.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get current user",
        description="Retrieve the authenticated user's profile information.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update current user",
        description="Update the authenticated user's profile. Can update first_name, last_name, and phone.",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update current user",
        description="Partially update the authenticated user's profile.",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user