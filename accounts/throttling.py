from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class OTPRateThrottle(AnonRateThrottle):
    """
    Custom throttle for OTP-related endpoints to prevent abuse.
    Limits to 5 requests per hour for anonymous users.
    """
    scope = 'otp'


class AuthRateThrottle(AnonRateThrottle):
    """
    Custom throttle for authentication endpoints (login, register, etc.).
    More generous than default anon throttle to allow legitimate login attempts.
    Limits to 30 requests per minute for anonymous users.
    """
    scope = 'auth'
