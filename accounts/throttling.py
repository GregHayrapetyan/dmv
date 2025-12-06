from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class OTPRateThrottle(AnonRateThrottle):
    """
    Custom throttle for OTP-related endpoints to prevent abuse.
    Limits to 5 requests per hour for anonymous users.
    """
    scope = 'otp'
