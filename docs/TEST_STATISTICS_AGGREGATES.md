# Test Statistics Aggregates Implementation

## Overview
Added aggregate statistics to the `/tests/statistics/` endpoint to show overall performance across all test attempts for the authenticated user.

## Changes Made

### 1. Updated `TestStatisticsView` (`learning/views.py`)
- Added `list()` method override to calculate aggregate statistics
- Aggregates are calculated across ALL test attempts for the authenticated user
- Response now includes both individual test stats and overall statistics

### 2. New Serializer (`learning/serializers.py`)
- Created `TestStatisticsWithAggregatesSerializer` to document the complete response structure
- Updated OpenAPI schema to reflect the new response format

## API Response Structure

### Endpoint: `GET /tests/statistics/`

**Authentication Required:** Yes

**Response Format:**
```json
{
  "tests": [
    {
      "id": 1,
      "title": "Road Signs Test",
      "image": "http://example.com/image.jpg",
      "question_count": 50,
      "best_percentage": 85.5,
      "best_correct_answers": 43,
      "best_incorrect_answers": 7
    },
    // ... more tests
  ],
  "total_questions_answered": 850,
  "total_correct_answers": 200,
  "total_incorrect_answers": 144,
  "correct_percentage": 23.53,
  "incorrect_percentage": 16.94
}
```

## Field Descriptions

### Aggregate Fields (New)
- **`total_questions_answered`**: Total number of questions answered across all test attempts
- **`total_correct_answers`**: Total number of correct answers across all test attempts
- **`total_incorrect_answers`**: Total number of incorrect answers across all test attempts
- **`correct_percentage`**: Percentage of correct answers (total_correct / total_questions * 100)
- **`incorrect_percentage`**: Percentage of incorrect answers (total_incorrect / total_questions * 100)

### Per-Test Fields (Existing)
- **`tests`**: Array of test statistics
  - **`id`**: Test ID
  - **`title`**: Test title
  - **`image`**: Test image URL
  - **`question_count`**: Number of questions in this test
  - **`best_percentage`**: User's best score percentage for this test
  - **`best_correct_answers`**: Correct answers from user's best attempt
  - **`best_incorrect_answers`**: Incorrect answers from user's best attempt

## Usage Example

### Dashboard Implementation
Use the aggregate fields to display overall statistics:

**Correct Answers Card:**
- Percentage: `correct_percentage` (e.g., 56%)
- Answered Questions: `total_questions_answered` (e.g., 850)
- Correct Answers: `total_correct_answers` (e.g., 200)

**Incorrect Answers Card:**
- Percentage: `incorrect_percentage` (e.g., 56%)
- Answered Questions: `total_questions_answered` (e.g., 850)
- Wrong Answers: `total_incorrect_answers` (e.g., 144)

## Notes
- Aggregate statistics are calculated from ALL test attempts by the user
- Percentages are rounded to 2 decimal places
- If user has no attempts, all aggregate values will be 0
- State filtering applies to the tests list, but aggregates include ALL attempts regardless of state
