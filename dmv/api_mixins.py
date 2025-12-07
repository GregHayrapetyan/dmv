"""
Custom mixins for standardized API responses in generic views.
"""

from rest_framework import status
from dmv.api_response import APIResponse


class StandardizedResponseMixin:
    """
    Mixin to wrap DRF generic view responses in standardized format.
    
    Use this with ListAPIView, RetrieveAPIView, etc. to automatically
    wrap responses in the standardized structure.
    """
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Override to wrap successful responses in standardized format"""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Only wrap successful responses (200-299)
        if 200 <= response.status_code < 300:
            # Check if already wrapped (has 'success' key)
            if isinstance(response.data, dict) and 'success' in response.data:
                return response
            
            # Wrap the response
            message = self.get_success_message(request, response)
            wrapped_response = APIResponse.success(
                data=response.data,
                message=message,
                status_code=response.status_code
            )
            
            # Copy over the wrapped data
            response.data = wrapped_response.data
            response.status_code = wrapped_response.status_code
        
        return response
    
    def get_success_message(self, request, response):
        """
        Get the success message for the response.
        Override this method in views to customize messages.
        """
        # Default messages based on HTTP method and status
        if request.method == 'GET':
            if response.status_code == status.HTTP_200_OK:
                return "Data retrieved successfully"
        elif request.method == 'POST':
            if response.status_code == status.HTTP_201_CREATED:
                return "Resource created successfully"
            return "Operation completed successfully"
        elif request.method in ['PUT', 'PATCH']:
            return "Resource updated successfully"
        elif request.method == 'DELETE':
            return "Resource deleted successfully"
        
        return "Success"
