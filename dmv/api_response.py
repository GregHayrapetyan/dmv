"""
Standardized API Response Utilities

This module provides a consistent response structure for all API endpoints.
All API responses should use these utilities to ensure uniformity across the application.

Response Structure:
{
    "success": true/false,
    "message": "Human-readable message",
    "data": {...} or [...],  # Only present on success
    "error": {               # Only present on failure
        "code": "ERROR_CODE",
        "message": "Error message",
        "details": {...}     # Optional additional error details
    },
    "meta": {                # Optional metadata
        "timestamp": "ISO 8601 timestamp",
        "version": "v1",
        ...
    }
}
"""

from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from typing import Any, Dict, Optional


class APIResponse:
    """Standardized API response builder"""
    
    API_VERSION = "v1"
    
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
            message: Success message
            status_code: HTTP status code (default: 200)
            meta: Optional metadata dictionary
            
        Returns:
            Response object with standardized success structure
            
        Example:
            return APIResponse.success(
                data={"user": user_data},
                message="User retrieved successfully"
            )
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
        }
        
        # Add metadata
        if meta is None:
            meta = {}
        
        meta.update({
            "timestamp": timezone.now().isoformat(),
            "version": APIResponse.API_VERSION,
        })
        
        response_data["meta"] = meta
        
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
            error_code: Machine-readable error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
            status_code: HTTP status code (default: 400)
            details: Optional additional error details (e.g., field-specific errors)
            meta: Optional metadata dictionary
            
        Returns:
            Response object with standardized error structure
            
        Example:
            return APIResponse.error(
                message="Invalid credentials",
                error_code="INVALID_CREDENTIALS",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        """
        response_data = {
            "success": False,
            "message": message,
            "error": {
                "code": error_code,
                "message": message,
            }
        }
        
        if details:
            response_data["error"]["details"] = details
        
        # Add metadata
        if meta is None:
            meta = {}
        
        meta.update({
            "timestamp": timezone.now().isoformat(),
            "version": APIResponse.API_VERSION,
        })
        
        response_data["meta"] = meta
        
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
            message: Success message
            meta: Optional metadata dictionary
            
        Returns:
            Response object with 201 status
        """
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            meta=meta
        )
    
    @staticmethod
    def no_content(
        message: str = "Operation completed successfully",
        meta: Optional[Dict] = None
    ) -> Response:
        """
        Create a 204 No Content response.
        
        Args:
            message: Success message
            meta: Optional metadata dictionary
            
        Returns:
            Response object with 204 status
        """
        return APIResponse.success(
            data=None,
            message=message,
            status_code=status.HTTP_204_NO_CONTENT,
            meta=meta
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
            details: Field-specific validation errors
            
        Returns:
            Response object with 400 status
        """
        return APIResponse.error(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
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
            resource_type: Type of resource that wasn't found
            
        Returns:
            Response object with 404 status
        """
        details = {"resource_type": resource_type} if resource_type else None
        return APIResponse.error(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
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
            details: Optional additional details
            
        Returns:
            Response object with 401 status
        """
        return APIResponse.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
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
            details: Optional additional details
            
        Returns:
            Response object with 403 status
        """
        return APIResponse.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
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
            details: Optional additional details
            
        Returns:
            Response object with 500 status
        """
        return APIResponse.error(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
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
            details: Optional additional details
            
        Returns:
            Response object with 503 status
        """
        return APIResponse.error(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
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
            details: Optional additional details (e.g., retry_after)
            
        Returns:
            Response object with 429 status
        """
        return APIResponse.error(
            message=message,
            error_code="TOO_MANY_REQUESTS",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
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
