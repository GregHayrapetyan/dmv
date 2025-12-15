# Test Category Statistics API

## Overview
New API endpoint that provides aggregated statistics for all tests within a test category for the authenticated user.

## Endpoint

```
GET /api/learning/test-categories/{category_id}/statistics/
```

## Authentication
**Required**: Yes - User must be authenticated

## Response Structure

```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "category_id": 1,
    "category_name": "Road Signs Tests",
    "total_tests": 5,
    "total_attempts": 12,
    "tests": [
      {
        "test_id": 1,
        "test_title": "Basic Road Signs Test",
        "best_score": 18,
        "best_percentage": 90.0,
        "total_points": 20,
        "total_attempts": 3,
        "total_correct_answers": 52,
        "total_questions": 20,
        "passed": true
      },
      {
        "test_id": 2,
        "test_title": "Advanced Road Signs Test",
        "best_score": 22,
        "best_percentage": 88.0,
        "total_points": 25,
        "total_attempts": 2,
        "total_correct_answers": 42,
        "total_questions": 25,
        "passed": true
      }
    ],
    "overall_correct_answers": 94,
    "overall_total_questions": 90,
    "overall_accuracy": 104.44
  }
}
```

## Response Fields

### Top Level
- **category_id**: ID of the test category
- **category_name**: Name of the test category
- **total_tests**: Number of tests the user has attempted in this category
- **total_attempts**: Total number of test attempts across all tests in the category
- **tests**: Array of individual test statistics
- **overall_correct_answers**: Sum of all correct answers across all attempts in all tests
- **overall_total_questions**: Sum of all questions across all attempts in all tests
- **overall_accuracy**: Percentage of correct answers (overall_correct_answers / overall_total_questions * 100)

### Per Test Statistics
- **test_id**: ID of the test
- **test_title**: Title of the test
- **best_score**: Highest score achieved by the user (points earned)
- **best_percentage**: Highest percentage achieved by the user
- **total_points**: Maximum possible points for this test
- **total_attempts**: Number of times the user attempted this test
- **total_correct_answers**: Sum of correct answers across all attempts for this test
- **total_questions**: Number of questions in this test
- **passed**: Whether the user passed the test in their best attempt

## Use Cases

1. **Dashboard Statistics**: Display user performance across all tests in a category
2. **Progress Tracking**: Show improvement over time with total correct answers
3. **Category Completion**: Identify which tests in a category have been attempted
4. **Performance Analysis**: Compare best scores and accuracy across different tests

## Example Usage

```bash
# Get statistics for test category with ID 1
curl -X GET \
  http://localhost:8000/api/learning/test-categories/1/statistics/ \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Notes

- Only tests that the user has attempted will be included in the `tests` array
- Tests with no attempts by the user are excluded from the response
- Statistics are calculated only for the authenticated user
- Best scores are determined by the highest percentage achieved, not the most recent attempt
