"""
Custom exception handler for DRF to use standardized API responses.
"""

import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError, NotFound, PermissionDenied, 
    AuthenticationFailed, NotAuthenticated, Throttled
)
from django.core.exceptions import ObjectDoesNotExist
from dmv.api_response import APIResponse, ErrorCodes

logger = logging.getLogger(__name__)


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
        logger.error(f"Unhandled exception in {context.get('view', '')}: {exc}", exc_info=True)
        return APIResponse.server_error(
            message="An unexpected error occurred"
        )
    
    # Extract clean error message from response data
    error_message = _extract_error_message(response.data, exc)
    
    # Now customize the response format for DRF exceptions
    if isinstance(exc, ValidationError):
        return APIResponse.validation_error(
            message=error_message
        )
    
    elif isinstance(exc, NotFound):
        return APIResponse.not_found(
            message=error_message
        )
    
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return APIResponse.unauthorized(
            message=error_message
        )
    
    elif isinstance(exc, PermissionDenied):
        return APIResponse.forbidden(
            message=error_message
        )
    
    elif isinstance(exc, Throttled):
        return APIResponse.too_many_requests(
            message=error_message
        )
    
    # For any other DRF exception, use generic error response
    return APIResponse.error(
        message=error_message,
        status_code=response.status_code
    )


def _extract_error_message(data, exc):
    """
    Extract a clean error message from DRF response data.
    
    Handles various error formats including:
    - Simple strings
    - {'detail': 'message'}
    - JWT token errors with nested structure
    - Validation errors with field-specific messages
    """
    # If data is a string, return it
    if isinstance(data, str):
        return data
    
    # If data is a dict, try to extract the main message
    if isinstance(data, dict):
        # JWT token errors have a 'detail' field with the main message
        if 'detail' in data:
            detail = data['detail']
            # Handle ErrorDetail objects (convert to string)
            return str(detail)
        
        # For validation errors, try to create a meaningful message
        if len(data) == 1:
            key, value = next(iter(data.items()))
            if isinstance(value, list) and len(value) > 0:
                return f"{key}: {str(value[0])}"
            return str(value)
        
        # Multiple field errors - return generic message
        return "Validation error"
    
    # If data is a list, get the first error
    if isinstance(data, list) and len(data) > 0:
        return str(data[0])
    
    # Fallback to exception string
    return str(exc) if str(exc) else "An error occurred"
