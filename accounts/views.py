from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import (
    LoginSerializer, RegisterSerializer, ConfirmEmailSerializer, RequestPasswordResetSerializer,
    ResetPasswordSerializer, GoogleLoginSerializer, UserSerializer,
)
from .throttling import OTPRateThrottle
from django.conf import settings
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
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
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Registration validation failed",
                details=serializer.errors
            )
        self.perform_create(serializer)
        return APIResponse.created(
            data=None,
            message="Registration successful. Please check your email for verification code."
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
        description="Authenticate with email/phone and password. Returns JWT access token and sets refresh token as httpOnly cookie.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
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
            400: OpenApiResponse(description="Invalid credentials or inactive user"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        ser = self.get_serializer(data=request.data)
        if not ser.is_valid():
            return APIResponse.error(
                message="Invalid credentials",
                error_code=ErrorCodes.INVALID_CREDENTIALS,
                status_code=status.HTTP_400_BAD_REQUEST,
                details=ser.errors
            )
        user = ser.validated_data["user"]
        tokens = RefreshToken.for_user(user)
        logger.info(f"User logged in: {user.email}")
        
        response = APIResponse.success(
            data={
                "access": str(tokens.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_email_verified": user.is_email_verified
                }
            },
            message="Login successful"
        )
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key='refresh_token',
            value=str(tokens),
            httponly=True,
            secure=not settings.DEBUG,  # True in production (HTTPS only)
            samesite='Lax',
            max_age=7*24*60*60,  # 7 days (match JWT_REFRESH_TOKEN_LIFETIME)
            path='/api/accounts/token/refresh/'
        )
        
        return response

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
        if not ser.is_valid():
            return APIResponse.validation_error(
                message="Validation failed",
                details=ser.errors
            )
        ser.save()
        return APIResponse.success(
            data=None,
            message="If this email exists, a reset code has been sent."
        )

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
        if not ser.is_valid():
            return APIResponse.validation_error(
                message="Email confirmation failed",
                details=ser.errors
            )
        ser.save()
        return APIResponse.success(
            data=None,
            message="Email confirmed successfully"
        )

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
        if not ser.is_valid():
            return APIResponse.validation_error(
                message="Password reset failed",
                details=ser.errors
            )
        ser.save()
        return APIResponse.success(
            data=None,
            message="Password updated successfully"
        )

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
            return APIResponse.service_unavailable(
                message="Google authentication is not configured."
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
                return APIResponse.validation_error(
                    message="Email not provided by Google."
                )
            
            # Check if email is verified by Google
            if not email_verified:
                logger.warning(f"Unverified email attempted Google login: {email}")
                return APIResponse.error(
                    message="Email not verified by Google.",
                    error_code=ErrorCodes.EMAIL_NOT_VERIFIED,
                    status_code=status.HTTP_400_BAD_REQUEST
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
            response = APIResponse.success(
                data={
                    "access": str(tokens.access_token),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_email_verified": user.is_email_verified
                    }
                },
                message="Google authentication successful"
            )
            
            # Set refresh token as httpOnly cookie
            response.set_cookie(
                key='refresh_token',
                value=str(tokens),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/api/accounts/token/refresh/'
            )
            
            return response
            
        except ValueError as e:
            # Token is expired or invalid format
            logger.error(f"Invalid token format: {str(e)}")
            return APIResponse.error(
                message="Invalid or expired Google token.",
                error_code=ErrorCodes.INVALID_TOKEN,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {str(e)}")
            return APIResponse.error(
                message="Invalid Google token.",
                error_code=ErrorCodes.INVALID_TOKEN,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Unexpected error in Google login: {str(e)}")
            return APIResponse.server_error(
                message="An error occurred during authentication."
            )

class MeView(StandardizedResponseMixin, generics.RetrieveUpdateAPIView):
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
        description="Update the authenticated user's profile. Can update first_name, last_name, and phone. Supports partial updates.",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def put(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from httpOnly cookie.
    
    The refresh token is automatically sent via cookie, so clients don't need
    to include it in the request body.
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Refresh access token",
        description="Refresh the access token using the refresh token stored in httpOnly cookie. Returns a new access token and optionally a new refresh token (if rotation is enabled).",
        request=None,  # No request body needed
        responses={
            200: OpenApiResponse(
                description="Token refreshed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        },
                    )
                ]
            ),
            401: OpenApiResponse(description="Refresh token not found or invalid"),
        },
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return APIResponse.error(
                message="Refresh token not found",
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Add refresh token to request data
        request.data._mutable = True if hasattr(request.data, '_mutable') else None
        request.data['refresh'] = refresh_token
        if request.data._mutable is not None:
            request.data._mutable = False
        
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken:
            return APIResponse.error(
                message="Invalid or expired refresh token",
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get new tokens
        response = APIResponse.success(
            data={"access": serializer.validated_data['access']},
            message="Token refreshed successfully"
        )
        
        # If rotation is enabled, update the refresh token cookie
        if 'refresh' in serializer.validated_data:
            response.set_cookie(
                key='refresh_token',
                value=serializer.validated_data['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/api/accounts/token/refresh/'
            )
        
        return response


class LogoutView(generics.GenericAPIView):
    """
    Logout user by clearing the refresh token cookie.
    
    This invalidates the refresh token stored in the httpOnly cookie.
    The client should also discard the access token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Logout user",
        description="Clear the refresh token cookie to logout the user. Client should also discard the access token.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Logged out successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Logged out successfully"},
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        response = APIResponse.success(
            data=None,
            message="Logged out successfully"
        )
        response.delete_cookie('refresh_token', path='/api/accounts/token/refresh/')
        logger.info(f"User logged out: {request.user.email}")
        return response