# Terminology Changes: Score/Points → Correct/Incorrect Answers

## Summary
Replaced "score" and "points" terminology throughout the codebase with more intuitive terms: "correct answers", "incorrect answers", and "questions count".

## Changes Made

### 1. Models (`learning/models.py`)

#### Question Model
- **Removed field**: `points` (no longer needed - all questions count equally)
  - Removed constraint: `question_points_positive`

#### TestAttempt Model
- **Renamed field**: `score` → `correct_answers`
- **Renamed field**: `total_points` → `questions_count`
- **Added field**: `incorrect_answers` (PositiveIntegerField)

### 2. Serializers (`learning/serializers.py`)

Updated all serializers to use new field names:

#### QuestionSerializer & QuestionDetailSerializer
- Removed `points` field (not needed)

#### TestListSerializer
- Changed `best_score` → `best_correct_answers`
- Changed `best_total_points` → `best_incorrect_answers`
- Updated method names and return values accordingly

#### TestResultSerializer
- Changed `score` → `correct_answers`
- Changed `total_points` → `questions_count`
- Added `incorrect_answers` field

#### TestAttemptSerializer & TestAttemptListSerializer
- Changed `score` → `correct_answers`
- Changed `total_points` → `questions_count`
- Added `incorrect_answers` field

#### TestAttemptListWithStatsSerializer
- Added `total_incorrect_answers` field
- Updated help text for all fields

#### TestStatisticsSerializer
- Changed `best_score` → `best_correct_answers`
- Changed `best_total_points` → `best_incorrect_answers`
- Updated method names and return values

### 3. Views (`learning/views.py`)

#### TestSubmitView
- Replaced `score` and `total_points` calculation with `correct_answers`, `incorrect_answers`, and `questions_count`
- Updated logic to count incorrect answers (including unanswered questions)
- Changed percentage calculation to use `correct_answers / questions_count`
- Updated API response example in OpenAPI schema
- Updated log messages to use new terminology

#### UserTestAttemptsListView
- Updated aggregation to use `correct_answers`, `incorrect_answers`, and `questions_count`
- Added `total_incorrect_answers` to response data

### 4. Admin (`learning/admin.py`)

#### QuestionInline & QuestionAdmin
- Removed `points` field from fields and list_display

#### TestAttemptAdmin
- Changed list_display: `score`, `total_points` → `correct_answers`, `incorrect_answers`, `questions_count`
- Updated readonly_fields accordingly

### 5. Database Migration

Created migration `0012_rename_score_points_to_answers_count.py`:

1. Removes old constraint `question_points_positive`
2. Removes `Question.points` field (not needed - all questions count equally)
3. Renames `TestAttempt.score` → `TestAttempt.correct_answers`
4. Renames `TestAttempt.total_points` → `TestAttempt.questions_count`
5. Adds new field `TestAttempt.incorrect_answers`
6. Runs data migration to calculate `incorrect_answers = questions_count - correct_answers`

## API Response Changes

### Before:
```json
{
  "attempt_id": 1,
  "score": 8,
  "total_points": 10,
  "percentage": 80.0,
  "passed": true
}
```

### After:
```json
{
  "attempt_id": 1,
  "correct_answers": 8,
  "incorrect_answers": 2,
  "questions_count": 10,
  "percentage": 80.0,
  "passed": true
}
```

## Migration Instructions

To apply these changes to your database:

```bash
source venv/bin/activate
python manage.py migrate learning
```

The migration will:
- Preserve all existing data
- Automatically calculate `incorrect_answers` for existing test attempts
- Rename fields without data loss

## Breaking Changes

⚠️ **API Breaking Changes**: Frontend applications using the API will need to update their code to use the new field names:
- `score` → `correct_answers`
- `total_points` → `questions_count`
- New field: `incorrect_answers`
- `points` field removed from Question (all questions count equally)

## Benefits

1. **More intuitive**: "correct answers" and "incorrect answers" are clearer than "score" and "points"
2. **Better tracking**: Now explicitly tracking incorrect answers, not just deriving them
3. **Consistent terminology**: All references to scoring now use the same language
4. **User-friendly**: Terminology matches what users naturally understand
