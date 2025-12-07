"""
Custom permissions for learning content.
"""
from rest_framework import permissions
from accounts.models import Subscription


class HasActiveSubscriptionOrDemo(permissions.BasePermission):
    """
    Permission to check if user has active subscription or content is demo.
    """
    
    message = "Active subscription required to access this content."
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has access to the object (lesson or test).
        - Demo content is accessible to everyone
        - Premium content requires active subscription
        """
        # Allow if content is demo (for tests)
        if hasattr(obj, 'is_demo') and obj.is_demo:
            return True
        
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has active subscription
        try:
            subscription = Subscription.objects.get(user=request.user)
            return subscription.has_access()
        except Subscription.DoesNotExist:
            return False


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
