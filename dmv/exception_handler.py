"""
Custom exception handler for DRF to use standardized API responses.
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError, NotFound, PermissionDenied, 
    AuthenticationFailed, NotAuthenticated, Throttled
)
from django.core.exceptions import ObjectDoesNotExist
from dmv.api_response import APIResponse, ErrorCodes


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns standardized API responses.
    
    This handler catches all exceptions and formats them using our
    standardized APIResponse structure.
    """
    
    # Call DRF's default exception handler first to get the standard error response
    response = drf_exception_handler(exc, context)
    
    # If DRF didn't handle it, we handle it
    if response is None:
        # Handle Django's ObjectDoesNotExist
        if isinstance(exc, ObjectDoesNotExist):
            return APIResponse.not_found(
                message=str(exc) or "Resource not found"
            )
        
        # Handle any other unexpected exceptions
        return APIResponse.server_error(
            message="An unexpected error occurred"
        )
    
    # Now customize the response format for DRF exceptions
    if isinstance(exc, ValidationError):
        return APIResponse.validation_error(
            message="Validation error",
            details=response.data
        )
    
    elif isinstance(exc, NotFound):
        return APIResponse.not_found(
            message=str(exc) if str(exc) else "Resource not found"
        )
    
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return APIResponse.unauthorized(
            message=str(exc) if str(exc) else "Authentication required"
        )
    
    elif isinstance(exc, PermissionDenied):
        return APIResponse.forbidden(
            message=str(exc) if str(exc) else "Permission denied"
        )
    
    elif isinstance(exc, Throttled):
        return APIResponse.too_many_requests(
            message="Too many requests. Please try again later.",
            details={"retry_after": exc.wait} if hasattr(exc, 'wait') else None
        )
    
    # For any other DRF exception, use generic error response
    return APIResponse.error(
        message=str(exc) if str(exc) else "An error occurred",
        error_code="ERROR",
        status_code=response.status_code,
        details=response.data if isinstance(response.data, dict) else {"detail": response.data}
    )
