"""
Custom permissions for learning content.
"""
from rest_framework import permissions, status
from accounts.apple_iap_service import AppleIAPError, AppleIAPService
from accounts.models import Subscription
from dmv.api_response import APIResponse, ErrorCodes

APPLE_TRANSACTION_HEADER = "X-Apple-Signed-Transaction"


class HasActiveSubscription(permissions.BasePermission):
    """
    Permission to check if user has an active subscription.
    Used for endpoints that always require subscription.
    """
    
    message = "Active subscription required."
    
    def has_permission(self, request, view):
        """Check if user has active subscription."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            subscription = Subscription.objects.get(user=request.user)
            return subscription.has_access()
        except Subscription.DoesNotExist:
            return False


def has_premium_access(request):
    if request.user.is_authenticated:
        try:
            if Subscription.objects.get(user=request.user).has_access():
                return True
        except Subscription.DoesNotExist:
            pass

    signed_transaction = request.headers.get(APPLE_TRANSACTION_HEADER)
    if not signed_transaction:
        return False
    try:
        AppleIAPService.verify_active_transaction(signed_transaction)
    except AppleIAPError:
        return False
    return True


def premium_access_error(request, message):
    if not request.user.is_authenticated and APPLE_TRANSACTION_HEADER not in request.headers:
        return APIResponse.error(
            message="Authentication required",
            error_code=ErrorCodes.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if not has_premium_access(request):
        return APIResponse.error(
            message=message,
            error_code=ErrorCodes.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return None
