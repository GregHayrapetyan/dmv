"""
Standardized API Response Utilities

This module provides a consistent response structure for all API endpoints.
All API responses should use these utilities to ensure uniformity across the application.

Response Structure:
{
    "success": true/false,
    "error": null or "Error message string",
    "data": {...} or [...] or null
}
"""

from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from typing import Any, Dict, Optional


class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a successful API response.
        
        Args:
            data: The response data (dict, list, or serializer data)
            message: Success message (deprecated, kept for backward compatibility)
            status_code: HTTP status code (default: 200)
            meta: Optional metadata dictionary (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with standardized success structure
            
        Example:
            return APIResponse.success(
                data={"user": user_data}
            )
        """
        response_data = {
            "success": True,
            "error": None,
            "data": data,
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict] = None,
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create an error API response.
        
        Args:
            message: Error message
            error_code: Machine-readable error code (deprecated, kept for backward compatibility)
            status_code: HTTP status code (default: 400)
            details: Optional additional error details (deprecated, kept for backward compatibility)
            meta: Optional metadata dictionary (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with standardized error structure
            
        Example:
            return APIResponse.error(
                message="Invalid credentials",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        """
        response_data = {
            "success": False,
            "error": message,
            "data": None,
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a 201 Created response.
        
        Args:
            data: The created resource data
            message: Success message (deprecated, kept for backward compatibility)
            meta: Optional metadata dictionary (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 201 status
        """
        return APIResponse.success(
            data=data,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def no_content(
        message: str = "Operation completed successfully",
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a 204 No Content response.
        
        Args:
            message: Success message (deprecated, kept for backward compatibility)
            meta: Optional metadata dictionary (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 204 status
        """
        return APIResponse.success(
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )
    
    @staticmethod
    def validation_error(
        message: str = "Validation error",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create a validation error response (400).
        
        Args:
            message: Error message
            details: Field-specific validation errors (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 400 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        resource_type: Optional[str] = None
    ) -> Response:
        """
        Create a not found error response (404).
        
        Args:
            message: Error message
            resource_type: Type of resource that wasn't found (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 404 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Authentication required",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create an unauthorized error response (401).
        
        Args:
            message: Error message
            details: Optional additional details (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 401 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(
        message: str = "Permission denied",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create a forbidden error response (403).
        
        Args:
            message: Error message
            details: Optional additional details (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 403 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def server_error(
        message: str = "Internal server error",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create a server error response (500).
        
        Args:
            message: Error message
            details: Optional additional details (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 500 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def service_unavailable(
        message: str = "Service temporarily unavailable",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create a service unavailable error response (503).
        
        Args:
            message: Error message
            details: Optional additional details (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 503 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @staticmethod
    def too_many_requests(
        message: str = "Too many requests",
        details: Optional[Dict] = None
    ) -> Response:
        """
        Create a rate limit error response (429).
        
        Args:
            message: Error message
            details: Optional additional details (deprecated, kept for backward compatibility)
            
        Returns:
            Response object with 429 status
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


# Common error codes for reference
class ErrorCodes:
    """Standard error codes used across the API"""
    
    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Resources
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    
    # Rate Limiting
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    MAX_ATTEMPTS_EXCEEDED = "MAX_ATTEMPTS_EXCEEDED"
    
    # Server
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Business Logic
    OPERATION_FAILED = "OPERATION_FAILED"
    INVALID_STATE = "INVALID_STATE"
