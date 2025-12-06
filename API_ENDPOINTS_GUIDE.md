# Learning API Endpoints - Quick Reference Guide

## 📚 Lesson Endpoints

### List Lesson Categories
```
GET /api/learning/categories/
Auth: Not required
```

### List Lessons
```
GET /api/learning/lessons/
Query params: ?category={id}
Auth: Not required
```

### Get Lesson Detail
```
GET /api/learning/lessons/{slug}/
Auth: Not required
```

### Track Lesson Progress
```
POST /api/learning/lessons/{lesson_id}/progress/
Auth: Required
Body: {
  "completed": true/false
}
Response: {
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

### Get My Lesson Progress
```
GET /api/learning/my-progress/
Auth: Required
Response: [
  {
    "id": 1,
    "lesson": 1,
    "lesson_title": "Road Signs Basics",
    "completed": true,
    "completed_at": "2025-12-06T12:00:00Z",
    "started_at": "2025-12-06T11:00:00Z"
  }
]
```

---

## 📝 Test Endpoints

### List Test Categories
```
GET /api/learning/test-categories/
Auth: Not required
```

### List Tests
```
GET /api/learning/tests/
Query params: 
  ?category={id}
  ?demo=true/false
Auth: Not required
Response includes: passing_percentage, max_attempts
```

### Get Test Detail
```
GET /api/learning/tests/{id}/
Auth: Not required
Response: {
  "id": 1,
  "title": "Road Signs Test",
  "description": "...",
  "passing_percentage": 70,
  "max_attempts": 3,
  "time_limit_seconds": 1800,
  "shuffle_questions": false,
  "shuffle_answers": false,
  "questions": [
    {
      "id": 1,
      "text": "What does this sign mean?",
      "image": "...",
      "question_type": "multiple_choice",
      "order": 1,
      "points": 1,
      "answer_options": [
        {
          "id": 1,
          "text": "Stop",
          "order": 1
        }
      ]
    }
  ]
}
```

### Submit Test
```
POST /api/learning/tests/{id}/submit/
Auth: Required ⚠️
Body: {
  "answers": {
    "1": 3,  // question_id: answer_option_id
    "2": 7,
    "3": 11
  },
  "time_taken_seconds": 450  // optional
}
Response: {
  "attempt_id": 1,
  "score": 8,
  "total_points": 10,
  "percentage": 80.0,
  "passed": true,
  "questions": [
    {
      "id": 1,
      "text": "...",
      "answer_options": [
        {
          "id": 1,
          "text": "Stop",
          "is_correct": true,
          "explanation": "..."
        }
      ]
    }
  ],
  "user_answers": {
    "1": 3,
    "2": 7
  }
}
```

**Notes:**
- Now requires authentication
- Checks max_attempts before allowing submission
- Uses test's passing_percentage (not hardcoded 70%)
- Saves attempt to database
- Returns attempt_id for future reference

---

## 📊 Progress & History Endpoints

### Get My Test Attempts
```
GET /api/learning/my-attempts/
Query params:
  ?test={id}        // filter by specific test
  ?passed=true/false // filter by pass/fail
Auth: Required
Response: [
  {
    "id": 1,
    "user": 1,
    "user_email": "user@example.com",
    "test": 1,
    "test_title": "Road Signs Test",
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

### Get Specific Attempt Details
```
GET /api/learning/my-attempts/{id}/
Auth: Required
Response: {
  "id": 1,
  "user": 1,
  "user_email": "user@example.com",
  "test": 1,
  "test_title": "Road Signs Test",
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
      "question_text": "What does this sign mean?",
      "selected_option": 3,
      "selected_option_text": "Stop",
      "is_correct": true
    }
  ]
}
```

**Note:** Users can only view their own attempts

---

## 🔐 Authentication Requirements

| Endpoint | Auth Required |
|----------|---------------|
| List Categories | ❌ No |
| List Lessons | ❌ No |
| Get Lesson Detail | ❌ No |
| Track Lesson Progress | ✅ Yes |
| Get My Progress | ✅ Yes |
| List Test Categories | ❌ No |
| List Tests | ❌ No |
| Get Test Detail | ❌ No |
| Submit Test | ✅ Yes (NEW) |
| Get My Attempts | ✅ Yes |
| Get Attempt Detail | ✅ Yes |

---

## 🎯 Common Use Cases

### 1. Student Takes a Test
```
1. GET /api/learning/tests/{id}/          // Get test questions
2. POST /api/learning/tests/{id}/submit/  // Submit answers
3. GET /api/learning/my-attempts/         // View all attempts
```

### 2. Track Learning Progress
```
1. POST /api/learning/lessons/{id}/progress/  // Mark started
2. POST /api/learning/lessons/{id}/progress/  // Mark completed
3. GET /api/learning/my-progress/             // View all progress
```

### 3. Review Past Performance
```
1. GET /api/learning/my-attempts/?test={id}   // Get all attempts for a test
2. GET /api/learning/my-attempts/{id}/        // View detailed results
```

### 4. Check if Can Retake Test
```
1. GET /api/learning/tests/{id}/              // Check max_attempts
2. GET /api/learning/my-attempts/?test={id}   // Count existing attempts
3. If count < max_attempts: POST /api/learning/tests/{id}/submit/
```

---

## ⚠️ Error Responses

### Max Attempts Exceeded
```
POST /api/learning/tests/{id}/submit/
Response: 400 Bad Request
{
  "error": "Maximum attempts (3) reached for this test"
}
```

### Unauthenticated
```
POST /api/learning/tests/{id}/submit/
Response: 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}
```

### Invalid Answer Option
```
POST /api/learning/tests/{id}/submit/
Response: 200 OK (logged as warning)
// Invalid answers are skipped, not counted as correct
```

---

## 📈 New Features Summary

✅ **User Progress Tracking** - Track lesson completion
✅ **Test Attempt History** - Complete history of all attempts
✅ **Max Attempts Enforcement** - Configurable per test
✅ **Custom Passing Grades** - Each test has its own threshold
✅ **Time Tracking** - Optional time_taken_seconds
✅ **Detailed Results** - Review each answer
✅ **Security** - Users can only access their own data
✅ **Question Types** - Support for multiple choice and true/false

---

**Last Updated:** December 6, 2025
