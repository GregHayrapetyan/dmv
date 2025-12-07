"""
Test script to demonstrate standardized API responses.
Run this to see examples of the new response structure.
"""

import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmv.settings')
django.setup()

from dmv.api_response import APIResponse, ErrorCodes
from rest_framework import status


def print_response(title, response):
    """Pretty print a response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Data:")
    import json
    print(json.dumps(response.data, indent=2, default=str))


def test_success_responses():
    """Test various success responses"""
    print("\n" + "="*60)
    print("SUCCESS RESPONSES")
    print("="*60)
    
    # Simple success
    response = APIResponse.success(
        data={"user_id": 123, "email": "user@example.com"},
        message="User retrieved successfully"
    )
    print_response("1. Simple Success (200)", response)
    
    # Created
    response = APIResponse.created(
        data={"id": 456, "name": "New Resource"},
        message="Resource created successfully"
    )
    print_response("2. Created (201)", response)
    
    # No content
    response = APIResponse.no_content(
        message="Resource deleted successfully"
    )
    print_response("3. No Content (204)", response)


def test_error_responses():
    """Test various error responses"""
    print("\n" + "="*60)
    print("ERROR RESPONSES")
    print("="*60)
    
    # Validation error
    response = APIResponse.validation_error(
        message="Validation failed",
        details={
            "email": ["This field is required"],
            "password": ["Password must be at least 8 characters"]
        }
    )
    print_response("1. Validation Error (400)", response)
    
    # Not found
    response = APIResponse.not_found(
        message="User not found",
        resource_type="User"
    )
    print_response("2. Not Found (404)", response)
    
    # Unauthorized
    response = APIResponse.unauthorized(
        message="Authentication required"
    )
    print_response("3. Unauthorized (401)", response)
    
    # Forbidden
    response = APIResponse.forbidden(
        message="You don't have permission to perform this action"
    )
    print_response("4. Forbidden (403)", response)
    
    # Custom error
    response = APIResponse.error(
        message="Maximum attempts exceeded",
        error_code=ErrorCodes.MAX_ATTEMPTS_EXCEEDED,
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"max_attempts": 3, "current_attempts": 3}
    )
    print_response("5. Custom Error (400)", response)
    
    # Server error
    response = APIResponse.server_error(
        message="An unexpected error occurred"
    )
    print_response("6. Server Error (500)", response)
    
    # Service unavailable
    response = APIResponse.service_unavailable(
        message="Service temporarily unavailable"
    )
    print_response("7. Service Unavailable (503)", response)
    
    # Rate limit
    response = APIResponse.too_many_requests(
        message="Too many requests. Please try again later.",
        details={"retry_after": 3600}
    )
    print_response("8. Too Many Requests (429)", response)


def test_real_world_examples():
    """Test real-world API scenarios"""
    print("\n" + "="*60)
    print("REAL-WORLD EXAMPLES")
    print("="*60)
    
    # Login success
    response = APIResponse.success(
        data={
            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_email_verified": True
            }
        },
        message="Login successful"
    )
    print_response("1. Login Success", response)
    
    # Invalid credentials
    response = APIResponse.error(
        message="Invalid credentials",
        error_code=ErrorCodes.INVALID_CREDENTIALS,
        status_code=status.HTTP_400_BAD_REQUEST
    )
    print_response("2. Invalid Credentials", response)
    
    # Test submission success
    response = APIResponse.success(
        data={
            "attempt_id": 789,
            "score": 8,
            "total_points": 10,
            "percentage": 80.0,
            "passed": True
        },
        message="Test submitted successfully"
    )
    print_response("3. Test Submission Success", response)
    
    # Max attempts exceeded
    response = APIResponse.error(
        message="Maximum attempts (3) reached for this test",
        error_code=ErrorCodes.MAX_ATTEMPTS_EXCEEDED,
        status_code=status.HTTP_400_BAD_REQUEST
    )
    print_response("4. Max Attempts Exceeded", response)


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# STANDARDIZED API RESPONSE EXAMPLES")
    print("#"*60)
    
    test_success_responses()
    test_error_responses()
    test_real_world_examples()
    
    print("\n" + "#"*60)
    print("# All response structures follow the same pattern:")
    print("# - success: boolean")
    print("# - message: string")
    print("# - data: object (on success)")
    print("# - error: object (on failure)")
    print("# - meta: object (timestamp, version)")
    print("#"*60)
    print("\nFor more information, see:")
    print("  - /API_RESPONSE_STANDARD.md (full documentation)")
    print("  - /API_QUICK_REFERENCE.md (quick reference)")
    print("  - /STANDARDIZATION_SUMMARY.md (implementation summary)")
    print()


if __name__ == "__main__":
    main()
