# State-Specific Filtering Implementation

## Overview
Implemented state-specific filtering for lessons and tests based on user profile state selection. Users now only see content relevant to their selected US state.

## Changes Made

### 1. Database Models (`learning/models.py`)

#### Lesson Model
- Added `states` ManyToManyField linking to `onboarding.State`
- Allows lessons to be assigned to one or multiple states
- Empty = available for all states

#### Test Model
- Added `states` ManyToManyField linking to `onboarding.State`
- Allows tests to be assigned to one or multiple states
- Empty = available for all states

### 2. Views (`learning/views.py`)

#### LessonListView
- Updated `get_queryset()` to filter by authenticated user's profile state
- Shows lessons assigned to user's state OR lessons with no state assignment
- Uses Django Q objects for OR logic with `.distinct()` to avoid duplicates

#### TestListView
- Updated `get_queryset()` to filter by authenticated user's profile state
- Shows tests assigned to user's state OR tests with no state assignment
- Uses Django Q objects for OR logic with `.distinct()` to avoid duplicates

### 3. Admin Interface (`learning/admin.py`)

#### LessonAdmin
- Added `filter_horizontal` widget for easy state selection
- Added `states` to `list_filter` for filtering in admin list view
- Provides intuitive multi-select interface for assigning states

#### TestAdmin
- Added `filter_horizontal` widget for easy state selection
- Added `states` to `list_filter` for filtering in admin list view
- Added new "State Availability" fieldset in the form
- Provides intuitive multi-select interface for assigning states

### 4. Serializers (`learning/serializers.py`)

Added `state_names` field to the following serializers:
- `LessonListSerializer` - Shows which states lesson is available for
- `LessonDetailSerializer` - Shows which states lesson is available for
- `TestListSerializer` - Shows which states test is available for
- `TestDetailSerializer` - Shows which states test is available for

Returns empty list `[]` if available for all states.

### 5. Database Migration

Created migration: `learning/migrations/0005_lesson_states_test_states.py`
- Adds `lesson_states` many-to-many table
- Adds `test_states` many-to-many table

## How It Works

### For Administrators
1. Go to Django Admin
2. Edit a Lesson or Test
3. Select one or more states in the "States" field
4. Leave empty to make available for all states
5. Save

### For Users
1. User sets their state in their profile (`/api/onboarding/profile/`)
2. When user requests lessons or tests:
   - If user has a state set: Only content for their state + content with no state assignment
   - If user has no state set: All content
   - If user is not authenticated: All content (for public endpoints)

### API Response Examples

#### Lesson with specific states:
```json
{
  "id": 1,
  "title": "California Road Signs",
  "state_names": ["California"],
  ...
}
```

#### Lesson available for all states:
```json
{
  "id": 2,
  "title": "General Driving Rules",
  "state_names": [],
  ...
}
```

## Technical Details

### Filtering Logic
```python
# Show content for user's state OR content with no state assignment
queryset = queryset.filter(
    models.Q(states=profile.state) | models.Q(states__isnull=True)
).distinct()
```

### Why ManyToMany?
- Flexibility: Some content may be relevant to multiple states
- Scalability: Easy to add/remove states without data migration
- Performance: Indexed relationships for fast queries

### Why `.distinct()`?
- ManyToMany joins can create duplicate rows
- `.distinct()` ensures each lesson/test appears only once in results

## Testing Recommendations

1. **Create test data:**
   - Lesson A: No states (available everywhere)
   - Lesson B: California only
   - Lesson C: Texas only
   - Lesson D: California + Texas

2. **Test scenarios:**
   - User with California state → sees A, B, D
   - User with Texas state → sees A, C, D
   - User with no state → sees all
   - Unauthenticated user → sees all

3. **Admin testing:**
   - Verify state selection widget works
   - Verify filtering in list view
   - Verify bulk operations

## Migration Instructions

Already completed:
```bash
source venv/bin/activate
python manage.py makemigrations learning
python manage.py migrate learning
```

## Future Enhancements

Potential improvements:
1. Add state filtering to lesson categories
2. Add analytics for state-specific content performance
3. Add state-specific pricing plans
4. Add state-specific notifications
5. Add state abbreviation field for shorter display

## Notes

- Backward compatible: Existing lessons/tests with no states remain available to all users
- No breaking changes to API structure
- Filtering is automatic and transparent to frontend
- Admin interface is intuitive and requires no training
