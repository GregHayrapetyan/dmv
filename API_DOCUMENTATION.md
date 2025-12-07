# MyTest DMV API - Complete Documentation

**Base URL:** `http://localhost:8000` (development)  
**API Version:** 1.0.0  
**Interactive Docs:** `http://localhost:8000/api/docs/` (Swagger UI)  
**OpenAPI Schema:** `http://localhost:8000/api/schema/`

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Profile](#user-profile)
3. [Onboarding](#onboarding)
4. [Lessons](#lessons)
5. [Tests](#tests)
6. [Progress Tracking](#progress-tracking)
7. [Error Responses](#error-responses)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

All authentication endpoints use JWT (JSON Web Tokens) for session management.

### Register New User

**POST** `/api/accounts/register/`

Create a new user account and send email verification code.

**Authentication:** Not required  
**Rate Limit:** 5 requests per hour

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "password": "SecurePass123!",
  "repeat_password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "detail": "Registration successful. Please check your email for verification code."
}
```

**Errors:**
- `400` - Passwords don't match, email already exists, or validation error
- `429` - Rate limit exceeded

---

### Confirm Email

**POST** `/api/accounts/email/confirm/`

Verify email address with the 6-digit OTP code sent during registration.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "detail": "Email confirmed"
}
```

**Errors:**
- `400` - Invalid or expired code

**Notes:**
- Code expires in 10 minutes
- User must verify email before logging in

---

### Login

**POST** `/api/accounts/login/`

Authenticate with email/phone and password. Returns JWT access and refresh tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "identifier": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Errors:**
- `400` - Invalid credentials or inactive user

**Notes:**
- `identifier` can be email or phone number
- Access token lifetime: 60 minutes (configurable)
- Refresh token lifetime: 7 days (configurable)

---

### Refresh Token

**POST** `/api/accounts/token/refresh/`

Get a new access token using a refresh token.

**Authentication:** Not required

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Notes:**
- Returns new access and refresh tokens
- Old refresh token is blacklisted

---

### Request Password Reset

**POST** `/api/accounts/password/forgot/`

Send a password reset code to the user's email.

**Authentication:** Not required  
**Rate Limit:** 5 requests per hour

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

**Response (200 OK):**
```json
{
  "detail": "If this email exists, a reset code has been sent."
}
```

**Errors:**
- `429` - Rate limit exceeded

**Notes:**
- Always returns 200 for security (doesn't reveal if email exists)
- Code expires in 10 minutes

---

### Reset Password

**POST** `/api/accounts/password/reset/`

Reset password using the verification code sent to email.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "code": "123456",
  "new_password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "detail": "Password updated"
}
```

**Errors:**
- `400` - Invalid or expired code, or password validation failed

---

### Google OAuth Login

**POST** `/api/accounts/google/`

Authenticate using Google ID token. Creates new user if doesn't exist.

**Authentication:** Not required

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_email_verified": true
  }
}
```

**Errors:**
- `400` - Invalid token or email not verified by Google
- `401` - Invalid or expired Google token
- `503` - Google OAuth not configured on server

**Notes:**
- Email is automatically verified
- Creates new user account if email doesn't exist

---

## User Profile

### Get Current User

**GET** `/api/accounts/me/`

Retrieve the authenticated user's profile information.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_email_verified": true,
  "date_joined": "2025-12-01T10:00:00Z"
}
```

**Errors:**
- `401` - Authentication required

---

### Update Current User

**PUT/PATCH** `/api/accounts/me/`

Update the authenticated user's profile.

**Authentication:** Required

**Request Body (PATCH):**
```json
{
  "first_name": "Jane",
  "phone": "+0987654321"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+0987654321",
  "is_email_verified": true,
  "date_joined": "2025-12-01T10:00:00Z"
}
```

**Errors:**
- `400` - Validation error
- `401` - Authentication required

**Notes:**
- Cannot update `email`, `is_email_verified`, or `date_joined`
- Use PATCH for partial updates, PUT for full updates

---

## Onboarding

### List All States

**GET** `/api/onboarding/states/`

Retrieve a list of all US states available for user profile selection.

**Authentication:** Not required

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "California"
  },
  {
    "id": 2,
    "name": "Texas"
  }
]
```

---

### Get User Profile

**GET** `/api/onboarding/profile/`

Retrieve the authenticated user's onboarding profile.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "state": 1,
  "vehicle": "car",
  "knowledge": "beginner"
}
```

**Errors:**
- `401` - Authentication required

**Notes:**
- Profile is auto-created when user registers
- `vehicle` options: `car`, `motorcycle`, `commercial`
- `knowledge` options: `beginner`, `intermediate`, `advanced`

---

### Update User Profile

**PUT/PATCH** `/api/onboarding/profile/`

Update the authenticated user's onboarding profile.

**Authentication:** Required

**Request Body (PATCH):**
```json
{
  "state": 1,
  "vehicle": "car",
  "knowledge": "intermediate"
}
```

**Response (200 OK):**
```json
{
  "state": 1,
  "vehicle": "car",
  "knowledge": "intermediate"
}
```

**Errors:**
- `400` - Validation error
- `401` - Authentication required

---

## Lessons

### List Lesson Categories

**GET** `/api/learning/categories/`

Retrieve all lesson categories.

**Authentication:** Not required

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Road Signs",
    "slug": "road-signs",
    "description": "Learn about traffic signs and their meanings"
  }
]
```

---

### List Lessons

**GET** `/api/learning/lessons/`

Retrieve all lessons. Optionally filter by category.

**Authentication:** Not required

**Query Parameters:**
- `category` (integer, optional) - Filter by category ID

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Road Signs Basics",
    "slug": "road-signs-basics",
    "category": 1,
    "category_name": "Road Signs",
    "lesson_type": "text",
    "order": 1,
    "duration_minutes": 15,
    "is_published": true
  }
]
```

**Notes:**
- Results are paginated (20 items per page)
- `lesson_type` options: `text`, `video`, `interactive`

---

### Get Lesson Detail

**GET** `/api/learning/lessons/{slug}/`

Retrieve full details of a specific lesson by its slug.

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Road Signs Basics",
  "slug": "road-signs-basics",
  "category": 1,
  "category_name": "Road Signs",
  "lesson_type": "text",
  "content": "# Introduction to Road Signs\n\nRoad signs are...",
  "video_url": "https://youtube.com/watch?v=...",
  "order": 1,
  "duration_minutes": 15,
  "created_at": "2025-12-01T10:00:00Z"
}
```

**Errors:**
- `404` - Lesson not found

---

## Tests

### List Test Categories

**GET** `/api/learning/test-categories/`

Retrieve all test categories.

**Authentication:** Not required

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Road Signs Test",
    "slug": "road-signs-test",
    "lesson_category": 1,
    "lesson_category_name": "Road Signs"
  }
]
```

---

### List Tests

**GET** `/api/learning/tests/`

Retrieve all tests. Can filter by category or demo status.

**Authentication:** Not required

**Query Parameters:**
- `category` (integer, optional) - Filter by test category ID
- `demo` (boolean, optional) - Filter by demo status (true/false)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Road Signs Practice Test",
    "lesson": 1,
    "lesson_title": "Road Signs Basics",
    "test_category": 1,
    "test_category_name": "Road Signs Test",
    "is_demo": false,
    "time_limit_seconds": 1800,
    "question_count": 20,
    "passing_percentage": 70,
    "max_attempts": 3
  }
]
```

**Notes:**
- Results are paginated (20 items per page)
- `max_attempts`: null means unlimited attempts

---

### Get Test Detail

**GET** `/api/learning/tests/{id}/`

Retrieve full test details with all questions and answer options.

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Road Signs Practice Test",
  "description": "Test your knowledge of road signs",
  "lesson": 1,
  "lesson_title": "Road Signs Basics",
  "test_category": 1,
  "test_category_name": "Road Signs Test",
  "time_limit_seconds": 1800,
  "is_demo": false,
  "passing_percentage": 70,
  "shuffle_questions": false,
  "shuffle_answers": false,
  "questions": [
    {
      "id": 1,
      "text": "What does a red octagon sign mean?",
      "image": "/media/signs/stop.jpg",
      "question_type": "multiple_choice",
      "order": 1,
      "points": 1,
      "answer_options": [
        {
          "id": 1,
          "text": "Stop",
          "order": 1
        },
        {
          "id": 2,
          "text": "Yield",
          "order": 2
        }
      ]
    }
  ]
}
```

**Errors:**
- `404` - Test not found

**Notes:**
- Correct answers are NOT included in the response
- `question_type` options: `multiple_choice`, `true_false`

---

### Submit Test

**POST** `/api/learning/tests/{id}/submit/`

Submit answers for a test. Returns score, percentage, pass/fail status, and correct answers.

**Authentication:** Required

**Request Body:**
```json
{
  "answers": {
    "1": 1,
    "2": 5,
    "3": 9
  },
  "time_taken_seconds": 450
}
```

**Response (200 OK):**
```json
{
  "attempt_id": 1,
  "score": 8,
  "total_points": 10,
  "percentage": 80.0,
  "passed": true,
  "questions": [
    {
      "id": 1,
      "text": "What does a red octagon sign mean?",
      "image": "/media/signs/stop.jpg",
      "question_type": "multiple_choice",
      "order": 1,
      "points": 1,
      "answer_options": [
        {
          "id": 1,
          "text": "Stop",
          "is_correct": true,
          "explanation": "A red octagon always means stop",
          "order": 1
        },
        {
          "id": 2,
          "text": "Yield",
          "is_correct": false,
          "explanation": "",
          "order": 2
        }
      ]
    }
  ],
  "user_answers": {
    "1": 1,
    "2": 5
  }
}
```

**Errors:**
- `400` - Max attempts exceeded or validation error
- `401` - Authentication required
- `404` - Test not found

**Notes:**
- `answers` is a dictionary mapping question_id to answer_option_id
- `time_taken_seconds` is optional
- Enforces `max_attempts` limit if configured
- Creates a `TestAttempt` record for history

---

## Progress Tracking

### Update Lesson Progress

**POST** `/api/learning/lessons/{lesson_id}/progress/`

Mark a lesson as started or completed.

**Authentication:** Required

**Request Body:**
```json
{
  "completed": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 1,
  "lesson": 1,
  "lesson_title": "Road Signs Basics",
  "completed": true,
  "completed_at": "2025-12-06T12:00:00Z",
  "started_at": "2025-12-06T11:00:00Z",
  "updated_at": "2025-12-06T12:00:00Z"
}
```

**Errors:**
- `401` - Authentication required
- `404` - Lesson not found

**Notes:**
- Creates progress record if it doesn't exist
- Automatically sets `started_at` on first call
- Sets `completed_at` when `completed` is true

---

### Get My Lesson Progress

**GET** `/api/learning/my-progress/`

Retrieve all lesson progress records for the authenticated user.

**Authentication:** Required

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": 1,
    "lesson": 1,
    "lesson_title": "Road Signs Basics",
    "completed": true,
    "completed_at": "2025-12-06T12:00:00Z",
    "started_at": "2025-12-06T11:00:00Z",
    "updated_at": "2025-12-06T12:00:00Z"
  }
]
```

**Errors:**
- `401` - Authentication required

---

### Get My Test Attempts

**GET** `/api/learning/my-attempts/`

Retrieve all test attempts for the authenticated user.

**Authentication:** Required

**Query Parameters:**
- `test` (integer, optional) - Filter by specific test ID
- `passed` (boolean, optional) - Filter by pass/fail status (true/false)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": 1,
    "user_email": "john.doe@example.com",
    "test": 1,
    "test_title": "Road Signs Practice Test",
    "score": 8,
    "total_points": 10,
    "percentage": "80.00",
    "passed": true,
    "time_taken_seconds": 450,
    "started_at": "2025-12-06T12:00:00Z",
    "completed_at": "2025-12-06T12:07:30Z"
  }
]
```

**Errors:**
- `401` - Authentication required

**Notes:**
- Results are ordered by most recent first
- Results are paginated (20 items per page)

---

### Get Test Attempt Details

**GET** `/api/learning/my-attempts/{id}/`

Retrieve detailed results of a specific test attempt.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 1,
  "user_email": "john.doe@example.com",
  "test": 1,
  "test_title": "Road Signs Practice Test",
  "score": 8,
  "total_points": 10,
  "percentage": "80.00",
  "passed": true,
  "time_taken_seconds": 450,
  "started_at": "2025-12-06T12:00:00Z",
  "completed_at": "2025-12-06T12:07:30Z",
  "answers": [
    {
      "id": 1,
      "question": 1,
      "question_text": "What does a red octagon sign mean?",
      "selected_option": 1,
      "selected_option_text": "Stop",
      "is_correct": true
    }
  ]
}
```

**Errors:**
- `401` - Authentication required
- `404` - Attempt not found or doesn't belong to user

**Notes:**
- Users can only view their own attempts
- Includes all answers with correctness information

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

### Common HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Validation error or invalid request
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

### Default Limits

- **Anonymous users:** 100 requests per hour
- **Authenticated users:** 1000 requests per hour
- **OTP endpoints:** 5 requests per hour (register, password reset)

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## Authentication Headers

For endpoints requiring authentication, include the JWT access token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## Pagination

List endpoints return paginated results:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/learning/lessons/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query Parameters:**
- `page` (integer) - Page number (default: 1)
- `page_size` (integer) - Items per page (default: 20, max: 100)

---

## Interactive API Documentation

Visit the interactive Swagger UI documentation at:

**http://localhost:8000/api/docs/**

Features:
- Browse all endpoints
- View request/response schemas
- Try out API calls directly from the browser
- See example requests and responses
- Download OpenAPI schema

---

## Quick Start Guide

### 1. Register and Login

```bash
# Register
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "password": "SecurePass123!",
    "repeat_password": "SecurePass123!"
  }'

# Confirm email
curl -X POST http://localhost:8000/api/accounts/email/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "code": "123456"
  }'

# Login
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 2. Browse Lessons

```bash
# List categories
curl http://localhost:8000/api/learning/categories/

# List lessons
curl http://localhost:8000/api/learning/lessons/

# Get lesson detail
curl http://localhost:8000/api/learning/lessons/road-signs-basics/
```

### 3. Take a Test

```bash
# Get test
curl http://localhost:8000/api/learning/tests/1/

# Submit test (requires authentication)
curl -X POST http://localhost:8000/api/learning/tests/1/submit/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "1": 1,
      "2": 5
    },
    "time_taken_seconds": 450
  }'
```

### 4. Track Progress

```bash
# Mark lesson as completed
curl -X POST http://localhost:8000/api/learning/lessons/1/progress/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# View my progress
curl http://localhost:8000/api/learning/my-progress/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# View my test attempts
curl http://localhost:8000/api/learning/my-attempts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Support

For issues or questions:
- Check the interactive docs at `/api/docs/`
- Review the OpenAPI schema at `/api/schema/`
- Contact the development team

---

**Last Updated:** December 7, 2025  
**API Version:** 1.0.0
