# API Documentation Guide

This project provides comprehensive API documentation in multiple formats to suit different needs.

## 📚 Documentation Formats

### 1. Interactive Swagger UI (Recommended)

The best way to explore and test the API is through the interactive Swagger UI:

**URL:** `http://localhost:8000/api/docs/`

**Features:**
- ✅ Browse all endpoints with detailed descriptions
- ✅ View request/response schemas and examples
- ✅ Try out API calls directly from your browser
- ✅ Automatic authentication handling
- ✅ Real-time validation
- ✅ Download OpenAPI schema

**How to use:**
1. Start the development server: `python manage.py runserver`
2. Open your browser and navigate to `http://localhost:8000/api/docs/`
3. Expand any endpoint to see details
4. Click "Try it out" to test endpoints
5. For authenticated endpoints, click "Authorize" and enter your JWT token

### 2. OpenAPI Schema (JSON)

Raw OpenAPI 3.0 schema for programmatic access or importing into tools:

**URL:** `http://localhost:8000/api/schema/`

**Use cases:**
- Import into Postman, Insomnia, or other API clients
- Generate client SDKs
- Automated testing
- API validation

**How to download:**
```bash
curl http://localhost:8000/api/schema/ > openapi-schema.json
```

### 3. Complete Documentation (Markdown)

Comprehensive written documentation with examples:

**File:** `API_DOCUMENTATION.md`

**Contents:**
- All endpoints with detailed descriptions
- Request/response examples
- Authentication guide
- Error handling
- Rate limiting
- Quick start guide
- Common use cases

**Best for:**
- Offline reference
- Onboarding new developers
- Understanding API concepts
- Copy-paste examples

### 4. Quick Reference Guide (Markdown)

Simplified endpoint reference for quick lookups:

**File:** `API_ENDPOINTS_GUIDE.md`

**Contents:**
- Endpoint URLs and methods
- Basic request/response formats
- Authentication requirements
- Common workflows

**Best for:**
- Quick lookups
- Endpoint discovery
- Integration planning

## 🚀 Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser
```

### Start the Server

```bash
python manage.py runserver
```

### Access Documentation

1. **Interactive Docs:** http://localhost:8000/api/docs/
2. **OpenAPI Schema:** http://localhost:8000/api/schema/
3. **Admin Panel:** http://localhost:8000/admin/

## 🔑 Authentication

Most endpoints require JWT authentication. Here's how to get started:

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
    "phone": "+1234567890",
    "password": "TestPass123!",
    "repeat_password": "TestPass123!"
  }'
```

### 2. Confirm Email

Check your console for the verification code (in development mode), then:

```bash
curl -X POST http://localhost:8000/api/accounts/email/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'
```

### 3. Login

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "password": "TestPass123!"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Use the Access Token

Include the access token in the Authorization header:

```bash
curl http://localhost:8000/api/accounts/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Or in Swagger UI:
1. Click the "Authorize" button at the top
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click "Authorize"

## 📋 API Endpoints Overview

### Authentication
- `POST /api/accounts/register/` - Register new user
- `POST /api/accounts/login/` - Login
- `POST /api/accounts/token/refresh/` - Refresh token
- `POST /api/accounts/email/confirm/` - Confirm email
- `POST /api/accounts/password/forgot/` - Request password reset
- `POST /api/accounts/password/reset/` - Reset password
- `POST /api/accounts/google/` - Google OAuth login
- `GET /api/accounts/me/` - Get current user
- `PUT/PATCH /api/accounts/me/` - Update current user

### Onboarding
- `GET /api/onboarding/states/` - List all states
- `GET /api/onboarding/profile/` - Get user profile
- `PUT/PATCH /api/onboarding/profile/` - Update user profile

### Lessons
- `GET /api/learning/categories/` - List lesson categories
- `GET /api/learning/lessons/` - List lessons
- `GET /api/learning/lessons/{slug}/` - Get lesson detail

### Tests
- `GET /api/learning/test-categories/` - List test categories
- `GET /api/learning/tests/` - List tests
- `GET /api/learning/tests/{id}/` - Get test detail
- `POST /api/learning/tests/{id}/submit/` - Submit test answers

### Progress
- `POST /api/learning/lessons/{id}/progress/` - Update lesson progress
- `GET /api/learning/my-progress/` - Get my lesson progress
- `GET /api/learning/my-attempts/` - Get my test attempts
- `GET /api/learning/my-attempts/{id}/` - Get test attempt details

## 🛠️ Tools & Integrations

### Postman

1. Import the OpenAPI schema:
   - Open Postman
   - Click "Import"
   - Select "Link" and paste: `http://localhost:8000/api/schema/`
   - Click "Continue" and "Import"

2. All endpoints will be automatically added to your Postman collection

### Insomnia

1. Import the OpenAPI schema:
   - Open Insomnia
   - Click "Create" → "Import From" → "URL"
   - Paste: `http://localhost:8000/api/schema/`
   - Click "Fetch and Import"

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/accounts/login/", json={
    "identifier": "test@example.com",
    "password": "TestPass123!"
})
tokens = response.json()
access_token = tokens["access"]

# Make authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/accounts/me/", headers=headers)
user = response.json()
print(user)
```

### JavaScript/TypeScript Client

```javascript
const BASE_URL = "http://localhost:8000";

// Login
const loginResponse = await fetch(`${BASE_URL}/api/accounts/login/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    identifier: "test@example.com",
    password: "TestPass123!"
  })
});
const { access } = await loginResponse.json();

// Make authenticated request
const userResponse = await fetch(`${BASE_URL}/api/accounts/me/`, {
  headers: { "Authorization": `Bearer ${access}` }
});
const user = await userResponse.json();
console.log(user);
```

## 📖 Additional Resources

- **Django REST Framework:** https://www.django-rest-framework.org/
- **drf-spectacular:** https://drf-spectacular.readthedocs.io/
- **JWT Authentication:** https://django-rest-framework-simplejwt.readthedocs.io/
- **OpenAPI Specification:** https://swagger.io/specification/

## 🐛 Troubleshooting

### "Authentication credentials were not provided"

Make sure you're including the Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### "Token is invalid or expired"

Your access token has expired (default: 60 minutes). Use the refresh token to get a new one:

```bash
curl -X POST http://localhost:8000/api/accounts/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### Swagger UI not loading

1. Make sure the server is running: `python manage.py runserver`
2. Check that `drf-spectacular` is installed: `pip install drf-spectacular`
3. Verify `INSTALLED_APPS` includes `'drf_spectacular'`
4. Clear browser cache and reload

### CORS errors in browser

If you're calling the API from a web app, make sure the frontend URL is in `CORS_ALLOWED_ORIGINS` in `settings.py`.

## 📝 Notes

- **Development Mode:** Email verification codes are printed to the console
- **Rate Limiting:** OTP endpoints (register, password reset) are limited to 5 requests per hour
- **Pagination:** List endpoints return 20 items per page by default
- **Token Lifetime:** Access tokens expire after 60 minutes, refresh tokens after 7 days

## 🤝 Contributing

When adding new endpoints:

1. Add `@extend_schema` decorator to the view
2. Include summary, description, and response examples
3. Update `API_DOCUMENTATION.md` with the new endpoint
4. Test the endpoint in Swagger UI
5. Verify the OpenAPI schema is correct

Example:

```python
from drf_spectacular.utils import extend_schema, OpenApiResponse

class MyView(APIView):
    @extend_schema(
        summary="Short description",
        description="Detailed description",
        responses={
            200: MySerializer,
            400: OpenApiResponse(description="Error description"),
        },
        tags=["Category"],
    )
    def get(self, request):
        # Implementation
        pass
```

---

**Happy coding! 🚀**
