from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from .serializers import (
    LoginSerializer, RegisterSerializer, ConfirmEmailSerializer, RequestPasswordResetSerializer,
    ResetPasswordSerializer, GoogleLoginSerializer, AppleLoginSerializer, UserSerializer, UserUpdateSerializer, SetAvatarSerializer,
    ChangePasswordSerializer,
)
from .throttling import AuthRateThrottle
from django.conf import settings
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
import logging
import time
import requests as http_requests
import jwt as pyjwt
from jwt import PyJWKClient, PyJWKClientError

logger = logging.getLogger(__name__)

# PyJWKClient fetches Google's JWKS keys once, then caches them in-memory
# for `lifespan` seconds.  Subsequent verify calls are pure local crypto
# with ZERO network round-trips, which is why this is fast.
_google_jwks_client = PyJWKClient(
    "https://www.googleapis.com/oauth2/v3/certs",
    cache_jwk_set=True,
    lifespan=3600,  # re-fetch keys at most once per hour
)

User = get_user_model()

@extend_schema_view(
    post=extend_schema(
        summary="Register new user",
        description="Create a new user account and send email verification code.",
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
        },
        tags=["Authentication"],
    )
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Creates a new user and sends a verification code to their email.
    The user must verify their email before they can log in.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

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
    throttle_classes = [AuthRateThrottle]

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
            secure=True,  # Required for SameSite=None
            samesite='None',  # Allow cross-origin cookies
            max_age=7*24*60*60,  # 7 days (match JWT_REFRESH_TOKEN_LIFETIME)
            path='/'
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
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        summary="Request password reset",
        description="Send a password reset code to the user's email.",
        request=RequestPasswordResetSerializer,
        responses={
            200: OpenApiResponse(
                description="Reset code sent (or email doesn't exist - security measure)",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "detail": "If this email exists, a reset code has been sent.",
                            "otp": "123456"
                        },
                    )
                ]
            ),
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
        otp_code = ser.save()
        return APIResponse.success(
            data={"otp": otp_code},
            message="If this email exists, a reset code has been sent."
        )

class ConfirmEmailView(generics.GenericAPIView):
    """
    Verify email address with OTP code.
    
    Confirms the user's email using the 6-digit code sent during registration.
    """
    serializer_class = ConfirmEmailSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

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
    throttle_classes = [AuthRateThrottle]

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
    throttle_classes = [AuthRateThrottle]

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
        """Accepts a Google id_token or access_token and returns app JWTs."""
        t0 = time.time()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        id_token_str = ser.validated_data.get("id_token")
        access_token = ser.validated_data.get("access_token")
        logger.info(f"[GOOGLE TIMING] Serializer validation: {time.time() - t0:.3f}s")
        
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            logger.error("Google OAuth Client ID not configured")
            return APIResponse.service_unavailable(
                message="Google authentication is not configured."
            )
        
        try:
            # Method 1: If ID token is provided (from GoogleLogin component)
            if id_token_str:
                t1 = time.time()
                # Verify the ID token locally using cached JWKS keys (no network call)
                signing_key = _google_jwks_client.get_signing_key_from_jwt(id_token_str)
                info = pyjwt.decode(
                    id_token_str,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience=settings.GOOGLE_OAUTH_CLIENT_ID,
                    issuer=["accounts.google.com", "https://accounts.google.com"],
                )
                logger.info(f"[GOOGLE TIMING] ID token verification: {time.time() - t1:.3f}s")
                
                # Extract user information from ID token
                email = info.get("email")
                email_verified = info.get("email_verified", False)
                first_name = info.get("given_name", "")
                last_name = info.get("family_name", "")
            
            # Method 2: If access token is provided (from useGoogleLogin hook)
            elif access_token:
                t1 = time.time()
                # Use access token to fetch user info from Google's userinfo endpoint
                userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                response = http_requests.get(userinfo_url, headers=headers, timeout=10)
                logger.info(f"[GOOGLE TIMING] Google userinfo API call: {time.time() - t1:.3f}s")
                
                if response.status_code != 200:
                    logger.error(f"Google userinfo fetch failed: {response.text}")
                    return APIResponse.error(
                        message="Invalid or expired Google access token.",
                        error_code=ErrorCodes.INVALID_TOKEN,
                        status_code=status.HTTP_401_UNAUTHORIZED
                    )
                
                info = response.json()
                
                # Extract user information from userinfo response
                email = info.get("email")
                email_verified = info.get("verified_email", False)
                first_name = info.get("given_name", "")
                last_name = info.get("family_name", "")
            
            else:
                return APIResponse.validation_error(
                    message="Either id_token or access_token must be provided."
                )
            
            # Validate required fields
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
            
            t2 = time.time()
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_email_verified": True,  # Google emails are pre-verified
                    "auth_provider": "google",
                }
            )
            logger.info(f"[GOOGLE TIMING] DB get_or_create: {time.time() - t2:.3f}s")
            
            # Update existing user's email verification status if not already verified
            if not created and not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                logger.info(f"Email verified via Google OAuth for existing user: {email}")
            
            if created:
                logger.info(f"New user created via Google OAuth: {email}")
            
            t3 = time.time()
            # Generate JWT tokens
            tokens = RefreshToken.for_user(user)
            logger.info(f"[GOOGLE TIMING] JWT token generation: {time.time() - t3:.3f}s")
            
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
                secure=True,  # Required for SameSite=None
                samesite='None',  # Allow cross-origin cookies
                max_age=7*24*60*60,
                path='/'
            )
            
            logger.info(f"[GOOGLE TIMING] Total endpoint time: {time.time() - t0:.3f}s")
            return response
            
        except (ValueError, pyjwt.InvalidTokenError) as e:
            # Token is expired, invalid format, bad signature, wrong audience, etc.
            logger.error(f"Invalid token: {str(e)}")
            return APIResponse.error(
                message="Invalid or expired Google token.",
                error_code=ErrorCodes.INVALID_TOKEN,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except PyJWKClientError as e:
            logger.error(f"Failed to fetch Google signing keys: {str(e)}")
            return APIResponse.server_error(
                message="Could not verify Google token. Please try again."
            )
        except (http_requests.ConnectionError, http_requests.Timeout) as e:
            logger.error(f"Network error verifying Google token: {str(e)}")
            return APIResponse.server_error(
                message="Could not reach Google servers. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error in Google login: {str(e)}")
            return APIResponse.server_error(
                message="An error occurred during authentication."
            )

class AppleLoginView(generics.GenericAPIView):
    """
    Authenticate with Apple Sign In.
    
    Accepts an Apple ID token, verifies it, and creates/authenticates the user.
    Returns JWT tokens for the application.
    """
    serializer_class = AppleLoginSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        summary="Apple Sign In login",
        description="Authenticate using Apple ID token. Creates new user if doesn't exist. Email is automatically verified.",
        request=AppleLoginSerializer,
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
            400: OpenApiResponse(description="Invalid token or email not verified by Apple"),
            401: OpenApiResponse(description="Invalid or expired Apple token"),
            503: OpenApiResponse(description="Apple OAuth not configured on server"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        """Accepts an Apple id_token and returns app JWTs."""
        import jwt
        import requests
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        
        id_token = ser.validated_data.get("id_token")
        user_data = ser.validated_data.get("user_data")
        
        # Check if Apple OAuth is configured
        if not all([settings.APPLE_CLIENT_ID, settings.APPLE_TEAM_ID, settings.APPLE_KEY_ID]):
            logger.error("Apple OAuth not properly configured")
            return APIResponse.service_unavailable(
                message="Apple authentication is not configured."
            )
        
        try:
            # Get Apple's public keys for verification
            apple_keys_url = "https://appleid.apple.com/auth/keys"
            response = requests.get(apple_keys_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Apple public keys: {response.text}")
                return APIResponse.error(
                    message="Failed to verify Apple token.",
                    error_code=ErrorCodes.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            apple_public_keys = response.json()
            
            # Decode token header to get key id (kid)
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            
            if not kid:
                logger.error("Apple token missing kid in header")
                return APIResponse.error(
                    message="Invalid Apple token format.",
                    error_code=ErrorCodes.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Find the matching public key
            public_key = None
            for key in apple_public_keys.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format for verification
                    from jwt.algorithms import RSAAlgorithm
                    public_key = RSAAlgorithm.from_jwk(key)
                    break
            
            if not public_key:
                logger.error(f"Apple public key not found for kid: {kid}")
                return APIResponse.error(
                    message="Invalid Apple token.",
                    error_code=ErrorCodes.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Verify and decode the token
            try:
                decoded_token = jwt.decode(
                    id_token,
                    public_key,
                    algorithms=['RS256'],
                    audience=settings.APPLE_ALLOWED_AUDIENCES,
                    issuer='https://appleid.apple.com',
                    options={'verify_exp': True}
                )
            except jwt.ExpiredSignatureError:
                logger.error("Apple token has expired")
                return APIResponse.error(
                    message="Apple token has expired.",
                    error_code=ErrorCodes.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            except jwt.InvalidTokenError as e:
                logger.error(f"Invalid Apple token: {str(e)}")
                return APIResponse.error(
                    message="Invalid Apple token.",
                    error_code=ErrorCodes.INVALID_TOKEN,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Extract user information from token
            apple_sub = decoded_token.get('sub')
            email = decoded_token.get('email')
            email_verified = decoded_token.get('email_verified', False)
            
            # Apple sends 'email_verified' as string "true" or boolean True
            if isinstance(email_verified, str):
                email_verified = email_verified.lower() == 'true'
            
            if not apple_sub:
                return APIResponse.validation_error(
                    message="Apple token missing sub claim."
                )
            
            # Extract name from user_data (only provided on first sign-in)
            first_name = ""
            last_name = ""
            
            if user_data and isinstance(user_data, dict):
                name = user_data.get('name', {})
                if isinstance(name, dict):
                    first_name = name.get('first_name', '')
                    last_name = name.get('last_name', '')
            
            # Look up user by Apple's stable identifier (sub) first
            created = False
            user = User.objects.filter(apple_sub=apple_sub).first()
            
            if user is None:
                # Fall back to email to link an existing account, or create a new one
                if not email:
                    return APIResponse.validation_error(
                        message="Email not provided by Apple."
                    )
                
                # Check if email is verified by Apple
                if not email_verified:
                    logger.warning(f"Unverified email attempted Apple login: {email}")
                    return APIResponse.error(
                        message="Email not verified by Apple.",
                        error_code=ErrorCodes.EMAIL_NOT_VERIFIED,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "is_email_verified": True,  # Apple emails are pre-verified
                        "auth_provider": "apple",
                        "apple_sub": apple_sub,
                    }
                )
                
                # Link Apple sub to existing account found by email
                if not created and not user.apple_sub:
                    user.apple_sub = apple_sub
                    user.save(update_fields=["apple_sub"])
                    logger.info(f"Linked Apple sub to existing user: {email}")
            
            # Update existing user's email verification status if not already verified
            if not created and not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                logger.info(f"Email verified via Apple Sign In for existing user: {user.email}")
            
            if created:
                logger.info(f"New user created via Apple Sign In: {email}")
            
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
                message="Apple authentication successful"
            )
            
            # Set refresh token as httpOnly cookie
            response.set_cookie(
                key='refresh_token',
                value=str(tokens),
                httponly=True,
                secure=True,
                samesite='None',
                max_age=7*24*60*60,
                path='/'
            )
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Failed to connect to Apple services: {str(e)}")
            return APIResponse.server_error(
                message="Failed to verify Apple token. Please try again later."
            )
        except Exception as e:
            logger.error(f"Unexpected error in Apple login: {str(e)}")
            return APIResponse.server_error(
                message="An error occurred during authentication."
            )

class MeView(StandardizedResponseMixin, generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    
    Returns the authenticated user's profile information.
    Allows updating first_name, last_name, phone, state, age, gender, and vehicle.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Use UserUpdateSerializer for PUT requests, UserSerializer for GET."""
        if self.request.method == 'PUT':
            return UserUpdateSerializer
        return UserSerializer

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
        description="Update the authenticated user's profile. Can update first_name, last_name, phone, state, age, gender, and vehicle. Supports partial updates.",
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def put(self, request, *args, **kwargs):
        kwargs['partial'] = True
        # Use UserUpdateSerializer for input validation
        serializer = UserUpdateSerializer(
            self.get_object(),
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Use UserSerializer for response to include all fields
        response_serializer = UserSerializer(
            self.get_object(),
            context={'request': request}
        )
        return APIResponse.success(
            data=response_serializer.data,
            message="Profile updated successfully"
        )

    @extend_schema(exclude=True)
    def patch(self, request, *args, **kwargs):
        return APIResponse.error(
            message="PATCH method not allowed. Use PUT instead.",
            error_code=ErrorCodes.METHOD_NOT_ALLOWED,
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def get_object(self):
        return self.request.user


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from httpOnly cookie.
    
    The refresh token is automatically sent via cookie, so clients don't need
    to include it in the request body.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = []  # No throttling on token refresh
    
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
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get('refresh_token')
            
            if not refresh_token:
                return APIResponse.error(
                    message="Refresh token not found",
                    error_code=ErrorCodes.AUTHENTICATION_FAILED,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Create a new data dict with the refresh token
            data = {'refresh': refresh_token}
            
            serializer = self.get_serializer(data=data)
            
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
                    secure=True,  # Required for SameSite=None
                    samesite='None',  # Allow cross-origin cookies
                    max_age=7*24*60*60,
                    path='/'
                )
            
            return response
        except Exception as e:
            logger.error(f"Unexpected error in token refresh: {str(e)}")
            return APIResponse.server_error(
                message="An unexpected error occurred"
            )


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
        
        # Delete refresh token cookie with matching parameters from login
        response.delete_cookie(
            key='refresh_token',
            path='/',
            samesite='None'
        )
        
        logger.info(f"User logged out: {request.user.email}")
        return response


class SetAvatarView(generics.GenericAPIView):
    """
    Set or update user avatar.
    
    Accepts an image file and saves it as the user's avatar.
    Replaces any existing avatar.
    """
    serializer_class = SetAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Set user avatar",
        description="""Upload and set the user's avatar image. 
        
        **Important:** This endpoint requires multipart/form-data content type.
        
        - Accepts JPEG, PNG, GIF, or WebP images
        - Maximum file size: 5MB
        - Field name: `avatar` (file upload)
        
        Example using curl:
        ```
        curl -X POST /api/accounts/set_avatar/ \\
          -H "Authorization: Bearer YOUR_TOKEN" \\
          -F "avatar=@/path/to/image.jpg"
        ```
        """,
        request=SetAvatarSerializer,
        responses={
            200: OpenApiResponse(
                description="Avatar updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "avatar_url": "/media/avatars/user_123_avatar.jpg"
                        },
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error (e.g., file too large, invalid format)"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def post(self, request):
        """Upload and set user avatar."""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Avatar upload validation failed",
                details=serializer.errors
            )
        
        user = request.user
        avatar_file = serializer.validated_data['avatar']
        
        # Delete old avatar if exists
        if user.avatar:
            try:
                user.avatar.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete old avatar for user {user.email}: {str(e)}")
        
        # Save new avatar
        user.avatar = avatar_file
        user.save(update_fields=['avatar'])
        
        logger.info(f"Avatar updated for user: {user.email}")
        
        # Return the avatar URL
        avatar_url = user.avatar.url if user.avatar else None
        
        return APIResponse.success(
            data={"avatar_url": avatar_url},
            message="Avatar updated successfully"
        )


class DeleteAccountView(generics.GenericAPIView):
    """
    Delete the authenticated user's account.
    
    Permanently deletes the user account and all associated data.
    This action cannot be undone.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Delete user account",
        description="""Permanently delete the authenticated user's account and all associated data.
        
        **Warning:** This action is irreversible. All user data, progress, and subscriptions will be deleted.
        
        The refresh token cookie will be cleared automatically.
        """,
        request=None,
        responses={
            200: OpenApiResponse(
                description="Account deleted successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Account deleted successfully"},
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def delete(self, request):
        """Delete the authenticated user's account."""
        user = request.user
        user_email = user.email
        
        try:
            # Delete the user account (cascade will handle related data)
            user.delete()
            
            logger.info(f"Account deleted: {user_email}")
            
            # Create response
            response = APIResponse.success(
                data=None,
                message="Account deleted successfully"
            )
            
            # Clear the refresh token cookie
            response.delete_cookie(
                key='refresh_token',
                path='/',
                samesite='None'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting account for {user_email}: {str(e)}")
            return APIResponse.server_error(
                message="Failed to delete account. Please try again later."
            )


class ChangePasswordView(generics.GenericAPIView):
    """
    Change the authenticated user's password.
    
    Requires the current password for verification and a new password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Change password",
        description="""Change the authenticated user's password.
        
        Requires:
        - old_password: Current password for verification (not required for Google/Apple auth users)
        - new_password: New password (minimum 8 characters)
        - confirm_password: Must match new_password
        
        The new password must be different from the old password.
        For users who registered via Google or Apple, old_password is not required.
        Setting a password will switch the user's auth_provider to 'email'.
        """,
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Password changed successfully"},
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error (e.g., passwords don't match, old password incorrect)"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=["User Profile"],
    )
    def post(self, request):
        """Change user password."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Password change validation failed",
                details=serializer.errors
            )
        
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        # If social auth user is setting a password, update auth_provider to 'email'
        was_social = user.auth_provider in ('google', 'apple')
        
        # Set the new password
        user.set_password(new_password)
        if was_social:
            user.auth_provider = 'email'
        user.save()
        
        if was_social:
            logger.info(f"Social auth user ({user.email}) set a password and switched to email auth")
        else:
            logger.info(f"Password changed for user: {user.email}")
        
        return APIResponse.success(
            data=None,
            message="Password changed successfully"
        )