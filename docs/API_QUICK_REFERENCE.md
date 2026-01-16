# API Response Standard - Quick Reference

## Import Statements

```python
from dmv.api_response import APIResponse, ErrorCodes
from dmv.api_mixins import StandardizedResponseMixin
```

## Response Methods Quick Reference

### Success Responses

```python
# Generic success (200)
APIResponse.success(
    data={"key": "value"},
    message="Operation successful"
)

# Created (201)
APIResponse.created(
    data={"id": 123},
    message="Resource created"
)

# No content (204)
APIResponse.no_content(
    message="Resource deleted"
)
```

### Error Responses

```python
# Validation error (400)
APIResponse.validation_error(
    message="Invalid input",
    details={"field": ["error message"]}
)

# Not found (404)
APIResponse.not_found(
    message="Resource not found",
    resource_type="User"
)

# Unauthorized (401)
APIResponse.unauthorized(
    message="Authentication required"
)

# Forbidden (403)
APIResponse.forbidden(
    message="Permission denied"
)

# Server error (500)
APIResponse.server_error(
    message="Internal server error"
)

# Service unavailable (503)
APIResponse.service_unavailable(
    message="Service temporarily unavailable"
)

# Too many requests (429)
APIResponse.too_many_requests(
    message="Rate limit exceeded",
    details={"retry_after": 3600}
)

# Custom error
APIResponse.error(
    message="Custom error message",
    error_code=ErrorCodes.OPERATION_FAILED,
    status_code=status.HTTP_400_BAD_REQUEST,
    details={"additional": "info"}
)
```

## Common Error Codes

```python
ErrorCodes.UNAUTHORIZED              # 401 - Authentication required
ErrorCodes.FORBIDDEN                 # 403 - Permission denied
ErrorCodes.INVALID_CREDENTIALS       # 400 - Invalid username/password
ErrorCodes.INVALID_TOKEN             # 401 - Invalid token
ErrorCodes.TOKEN_EXPIRED             # 401 - Token expired
ErrorCodes.EMAIL_NOT_VERIFIED        # 400 - Email not verified
ErrorCodes.VALIDATION_ERROR          # 400 - Validation failed
ErrorCodes.INVALID_INPUT             # 400 - Invalid input
ErrorCodes.MISSING_REQUIRED_FIELD    # 400 - Required field missing
ErrorCodes.NOT_FOUND                 # 404 - Resource not found
ErrorCodes.ALREADY_EXISTS            # 400 - Resource exists
ErrorCodes.CONFLICT                  # 409 - Resource conflict
ErrorCodes.TOO_MANY_REQUESTS         # 429 - Rate limit exceeded
ErrorCodes.MAX_ATTEMPTS_EXCEEDED     # 400 - Max attempts reached
ErrorCodes.INTERNAL_SERVER_ERROR     # 500 - Server error
ErrorCodes.SERVICE_UNAVAILABLE       # 503 - Service unavailable
ErrorCodes.OPERATION_FAILED          # 400 - Operation failed
ErrorCodes.INVALID_STATE             # 400 - Invalid state
```

## View Templates

### Custom APIView

```python
from rest_framework.views import APIView
from rest_framework import permissions
from dmv.api_response import APIResponse, ErrorCodes

class MyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Validate
        serializer = MySerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Validation failed",
                details=serializer.errors
            )
        
        # Process
        result = do_something(serializer.validated_data)
        
        # Return
        return APIResponse.success(
            data=result,
            message="Success"
        )
```

### List/Retrieve View with Mixin

```python
from rest_framework import generics, permissions
from dmv.api_mixins import StandardizedResponseMixin

class MyListView(StandardizedResponseMixin, generics.ListAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [permissions.AllowAny]
```

### Create View

```python
from rest_framework import generics, permissions
from dmv.api_response import APIResponse

class MyCreateView(generics.CreateAPIView):
    serializer_class = MySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.validation_error(
                message="Validation failed",
                details=serializer.errors
            )
        self.perform_create(serializer)
        return APIResponse.created(
            data=serializer.data,
            message="Resource created successfully"
        )
```

### Update View

```python
from rest_framework import generics, permissions
from dmv.api_mixins import StandardizedResponseMixin

class MyUpdateView(StandardizedResponseMixin, generics.UpdateAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    permission_classes = [permissions.IsAuthenticated]
```

## Common Patterns

### Check Authentication

```python
if not request.user.is_authenticated:
    return APIResponse.unauthorized(
        message="Please log in to continue"
    )
```

### Check Permissions

```python
if not user.has_permission():
    return APIResponse.forbidden(
        message="You don't have permission"
    )
```

### Handle Not Found

```python
try:
    obj = MyModel.objects.get(id=obj_id)
except MyModel.DoesNotExist:
    return APIResponse.not_found(
        message="Object not found",
        resource_type="MyModel"
    )
```

### Validate Serializer

```python
serializer = MySerializer(data=request.data)
if not serializer.is_valid():
    return APIResponse.validation_error(
        message="Validation failed",
        details=serializer.errors
    )
```

### Business Logic Error

```python
if some_condition_failed:
    return APIResponse.error(
        message="Operation cannot be completed",
        error_code=ErrorCodes.OPERATION_FAILED,
        status_code=status.HTTP_400_BAD_REQUEST
    )
```

## Response Structure

### Success Response

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...},
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {...}
  },
  "meta": {
    "timestamp": "2024-12-07T09:12:00Z",
    "version": "v1"
  }
}
```

## Checklist for New APIs

- [ ] Import `APIResponse` and/or `StandardizedResponseMixin`
- [ ] Use mixin for List/Retrieve views
- [ ] Use `APIResponse` methods for custom views
- [ ] Validate input before processing
- [ ] Return appropriate error codes
- [ ] Provide meaningful error messages
- [ ] Include error details when helpful
- [ ] Test response structure
- [ ] Document endpoint in OpenAPI schema

## Files Reference

- **Response utilities**: `/dmv/api_response.py`
- **Mixin**: `/dmv/api_mixins.py`
- **Exception handler**: `/dmv/exception_handler.py`
- **Full documentation**: `/API_RESPONSE_STANDARD.md`
