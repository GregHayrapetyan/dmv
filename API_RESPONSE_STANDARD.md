# API Response Standard Documentation

## Overview

All API endpoints in this application follow a standardized response structure to ensure consistency, predictability, and ease of integration. This document describes the response format, error handling, and best practices for creating new APIs.

## Table of Contents

1. [Response Structure](#response-structure)
2. [Success Responses](#success-responses)
3. [Error Responses](#error-responses)
4. [Error Codes Reference](#error-codes-reference)
5. [Creating New APIs](#creating-new-apis)
6. [Examples](#examples)

---

## Response Structure

### Standard Response Format

All API responses follow this structure:

```json
{
  "success": true/false,
  "message": "Human-readable message",
  "data": {...} or [...],     // Only present on success
  "error": {                   // Only present on failure
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {...}           // Optional additional error details
  },
  "meta": {                    // Optional metadata
    "timestamp": "ISO 8601 timestamp",
    "version": "v1",
    ...
  }
}
```

### Field Descriptions

- **success** (boolean): Indicates whether the request was successful
- **message** (string): Human-readable message describing the result
- **data** (object/array): The response payload (only in successful responses)
- **error** (object): Error information (only in failed responses)
  - **code** (string): Machine-readable error code
  - **message** (string): Human-readable error message
  - **details** (object): Additional error context (optional)
- **meta** (object): Metadata about the response
  - **timestamp** (string): ISO 8601 formatted timestamp
  - **version** (string): API version

---

## Success Responses

### HTTP 200 - OK

Used for successful GET, PUT, PATCH requests.

```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 201 - Created

Used for successful POST requests that create a resource.

```json
{
  "success": true,
  "message": "Resource created successfully",
  "data": {
    "id": 123,
    "name": "New Resource"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 204 - No Content

Used for successful DELETE requests or operations with no return data.

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": null,
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

---

## Error Responses

### HTTP 400 - Bad Request

Used for validation errors or invalid input.

```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation error",
    "details": {
      "email": ["This field is required"],
      "password": ["Password must be at least 8 characters"]
    }
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 401 - Unauthorized

Used when authentication is required but not provided or invalid.

```json
{
  "success": false,
  "message": "Authentication required",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 403 - Forbidden

Used when user is authenticated but doesn't have permission.

```json
{
  "success": false,
  "message": "Permission denied",
  "error": {
    "code": "FORBIDDEN",
    "message": "Permission denied"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 404 - Not Found

Used when a requested resource doesn't exist.

```json
{
  "success": false,
  "message": "Resource not found",
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {
      "resource_type": "User"
    }
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 429 - Too Many Requests

Used when rate limit is exceeded.

```json
{
  "success": false,
  "message": "Too many requests. Please try again later.",
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 3600
    }
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 500 - Internal Server Error

Used for unexpected server errors.

```json
{
  "success": false,
  "message": "Internal server error",
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Internal server error"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### HTTP 503 - Service Unavailable

Used when a service is temporarily unavailable.

```json
{
  "success": false,
  "message": "Service temporarily unavailable",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service temporarily unavailable"
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

---

## Error Codes Reference

### Authentication & Authorization

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Permission denied |
| `INVALID_CREDENTIALS` | 400 | Invalid username/password |
| `INVALID_TOKEN` | 401 | Invalid or malformed token |
| `TOKEN_EXPIRED` | 401 | Token has expired |
| `EMAIL_NOT_VERIFIED` | 400 | Email verification required |

### Validation

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_INPUT` | 400 | Invalid input data |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing |

### Resources

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `ALREADY_EXISTS` | 400 | Resource already exists |
| `CONFLICT` | 409 | Resource conflict |

### Rate Limiting

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TOO_MANY_REQUESTS` | 429 | Rate limit exceeded |
| `MAX_ATTEMPTS_EXCEEDED` | 400 | Maximum attempts reached |

### Server

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Business Logic

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `OPERATION_FAILED` | 400 | Operation failed |
| `INVALID_STATE` | 400 | Invalid state for operation |

---

## Creating New APIs

### Step 1: Import Required Utilities

```python
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
```

### Step 2: Choose the Right Approach

#### For Custom APIView or GenericAPIView

Use `APIResponse` helper methods directly:

```python
from rest_framework.views import APIView
from rest_framework import permissions
from dmv.api_response import APIResponse, ErrorCodes

class MyCustomView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Validate input
        serializer = MySerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid input",
                details=serializer.errors
            )
        
        # Process data
        result = process_data(serializer.validated_data)
        
        # Return success
        return APIResponse.success(
            data=result,
            message="Operation completed successfully"
        )
```

#### For List/Retrieve Views (ListAPIView, RetrieveAPIView, etc.)

Use `StandardizedResponseMixin`:

```python
from rest_framework import generics, permissions
from dmv.api_mixins import StandardizedResponseMixin

class MyListView(StandardizedResponseMixin, generics.ListAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [permissions.AllowAny]
    
    # The mixin automatically wraps the response
```

### Step 3: Handle Errors Properly

#### Validation Errors

```python
if not serializer.is_valid():
    return APIResponse.validation_error(
        message="Validation failed",
        details=serializer.errors
    )
```

#### Not Found Errors

```python
try:
    obj = MyModel.objects.get(id=obj_id)
except MyModel.DoesNotExist:
    return APIResponse.not_found(
        message="Object not found",
        resource_type="MyModel"
    )
```

#### Authentication Errors

```python
if not user.is_authenticated:
    return APIResponse.unauthorized(
        message="Please log in to continue"
    )
```

#### Permission Errors

```python
if not user.has_permission():
    return APIResponse.forbidden(
        message="You don't have permission to perform this action"
    )
```

#### Custom Business Logic Errors

```python
if attempt_count >= max_attempts:
    return APIResponse.error(
        message=f"Maximum attempts ({max_attempts}) exceeded",
        error_code=ErrorCodes.MAX_ATTEMPTS_EXCEEDED,
        status_code=status.HTTP_400_BAD_REQUEST
    )
```

### Step 4: Return Success Responses

#### Simple Success

```python
return APIResponse.success(
    data={"result": "value"},
    message="Operation successful"
)
```

#### Created Resource

```python
return APIResponse.created(
    data=serializer.data,
    message="Resource created successfully"
)
```

#### No Content

```python
return APIResponse.no_content(
    message="Resource deleted successfully"
)
```

---

## Examples

### Example 1: Login Endpoint

```python
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from dmv.api_response import APIResponse, ErrorCodes

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Validate credentials
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.error(
                message="Invalid credentials",
                error_code=ErrorCodes.INVALID_CREDENTIALS,
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors
            )
        
        # Get user and generate tokens
        user = serializer.validated_data["user"]
        tokens = RefreshToken.for_user(user)
        
        # Return success with tokens
        return APIResponse.success(
            data={
                "access": str(tokens.access_token),
                "refresh": str(tokens),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            },
            message="Login successful"
        )
```

### Example 2: List Endpoint with Mixin

```python
from rest_framework import generics, permissions
from dmv.api_mixins import StandardizedResponseMixin

class LessonListView(StandardizedResponseMixin, generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Lesson.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
    
    # Response is automatically wrapped by the mixin
```

### Example 3: Custom Business Logic

```python
from rest_framework.views import APIView
from rest_framework import permissions
from dmv.api_response import APIResponse, ErrorCodes

class TestSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, test_id):
        # Get test
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return APIResponse.not_found(
                message="Test not found",
                resource_type="Test"
            )
        
        # Check max attempts
        attempt_count = TestAttempt.objects.filter(
            user=request.user, 
            test=test
        ).count()
        
        if test.max_attempts and attempt_count >= test.max_attempts:
            return APIResponse.error(
                message=f"Maximum attempts ({test.max_attempts}) reached",
                error_code=ErrorCodes.MAX_ATTEMPTS_EXCEEDED,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate submission
        serializer = TestSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Invalid test submission",
                details=serializer.errors
            )
        
        # Process submission and calculate score
        result = process_test_submission(test, serializer.validated_data)
        
        # Return results
        return APIResponse.success(
            data=result,
            message="Test submitted successfully"
        )
```

---

## Best Practices

### 1. Always Use Standardized Responses

✅ **DO:**
```python
return APIResponse.success(data=result, message="Success")
```

❌ **DON'T:**
```python
return Response({"result": result})
```

### 2. Provide Meaningful Messages

✅ **DO:**
```python
return APIResponse.error(
    message="Email is already registered. Please use a different email or log in.",
    error_code=ErrorCodes.ALREADY_EXISTS
)
```

❌ **DON'T:**
```python
return APIResponse.error(message="Error", error_code="ERROR")
```

### 3. Include Relevant Error Details

✅ **DO:**
```python
return APIResponse.validation_error(
    message="Validation failed",
    details={
        "email": ["Invalid email format"],
        "password": ["Password must be at least 8 characters"]
    }
)
```

❌ **DON'T:**
```python
return APIResponse.validation_error(message="Invalid input")
```

### 4. Use Appropriate Error Codes

✅ **DO:**
```python
return APIResponse.error(
    message="Invalid credentials",
    error_code=ErrorCodes.INVALID_CREDENTIALS,
    status_code=status.HTTP_400_BAD_REQUEST
)
```

❌ **DON'T:**
```python
return APIResponse.error(
    message="Invalid credentials",
    error_code="ERROR"
)
```

### 5. Validate Before Processing

✅ **DO:**
```python
serializer = MySerializer(data=request.data)
if not serializer.is_valid():
    return APIResponse.validation_error(
        message="Validation failed",
        details=serializer.errors
    )
# Continue processing...
```

❌ **DON'T:**
```python
serializer = MySerializer(data=request.data)
serializer.is_valid(raise_exception=True)  # Let exception handler deal with it
```

### 6. Use Mixins for Generic Views

✅ **DO:**
```python
class MyListView(StandardizedResponseMixin, generics.ListAPIView):
    # ...
```

❌ **DON'T:**
```python
class MyListView(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse.success(data=response.data)  # Unnecessary
```

---

## Testing API Responses

When testing your APIs, verify:

1. **Response structure** matches the standard format
2. **Success field** is correctly set (true/false)
3. **Message** is meaningful and helpful
4. **Data** contains expected fields (on success)
5. **Error code** is appropriate (on failure)
6. **HTTP status code** matches the response type

Example test:

```python
def test_login_success(self):
    response = self.client.post('/api/accounts/login/', {
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.data['success'])
    self.assertIn('access', response.data['data'])
    self.assertIn('refresh', response.data['data'])
    self.assertEqual(response.data['message'], 'Login successful')
```

---

## Summary

- **All responses** use the standardized structure
- **Success responses** include `success: true`, `message`, and `data`
- **Error responses** include `success: false`, `message`, and `error` object
- **Use `APIResponse` helpers** for custom views
- **Use `StandardizedResponseMixin`** for generic views
- **Always provide meaningful messages** and appropriate error codes
- **Validate input** before processing
- **Handle exceptions** properly with appropriate error codes

For questions or clarifications, refer to the implementation in:
- `/dmv/api_response.py` - Response utilities
- `/dmv/api_mixins.py` - Mixin for generic views
- `/dmv/exception_handler.py` - Global exception handler
