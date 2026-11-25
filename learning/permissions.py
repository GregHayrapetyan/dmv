"""
Custom permissions for learning content.
"""
from rest_framework import permissions
from accounts.models import Subscription


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
