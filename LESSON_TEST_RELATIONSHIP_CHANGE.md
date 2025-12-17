# Lesson-Test Relationship Change

## Summary
Successfully reversed the relationship between `Lesson` and `Test` models. The `Test` model previously had a `OneToOneField` pointing to `Lesson`. Now the `Lesson` model has a `OneToOneField` pointing to `Test`.

## Changes Made

### 1. Models (`learning/models.py`)
- **Lesson Model**: Added `test` field as `OneToOneField` to `Test` with `related_name='lesson'`
- **Test Model**: Removed `lesson` field
- **Test Model**: Updated `__str__` method to handle the reversed relationship with try-except

### 2. Serializers (`learning/serializers.py`)
- **TestListSerializer**: Changed `lesson_title` from direct field access to `SerializerMethodField`
- **TestListSerializer**: Added `lesson_id` as `SerializerMethodField`
- **TestDetailSerializer**: Changed `lesson_title` from direct field access to `SerializerMethodField`
- **TestDetailSerializer**: Added `lesson_id` as `SerializerMethodField`
- Both serializers now use `get_lesson_title()` and `get_lesson_id()` methods with try-except to safely access the reversed relationship

### 3. Views (`learning/views.py`)
- **TestListView**: Removed `.select_related('lesson')` from queryset
- **TestDetailView**: Removed `.select_related('lesson')` from queryset
- **UserTestAttemptsListView**: Removed `'test__lesson'` from `.select_related()` call

### 4. Admin (`learning/admin.py`)
- **LessonAdmin**: Added `test` field to `list_display` and `raw_id_fields`
- **TestAdmin**: Removed `lesson` from `list_display`, `raw_id_fields`, and fieldsets
- **TestAdmin**: Added `get_lesson()` method to display the related lesson in admin list view

### 5. Migrations
Created three migrations to safely handle the relationship change:

1. **0009_add_test_to_lesson.py**: 
   - Adds the new `test` field to `Lesson` with `related_name='new_lesson'`
   - Makes the old `lesson` field on `Test` nullable with `related_name='old_test'`
   - Removes the index on the old `lesson` field

2. **0010_copy_lesson_test_relationship.py**: 
   - Data migration that copies all existing relationships from `Test.lesson` to `Lesson.test`
   - Includes reverse migration function for rollback

3. **0011_remove_lesson_from_test.py**: 
   - Removes the old `lesson` field from `Test`
   - Updates the `related_name` on `Lesson.test` to `'lesson'`

## Migration Strategy
The migration uses a three-step process to ensure data integrity:
1. Add the new field alongside the old one
2. Copy all existing data
3. Remove the old field

This approach ensures no data is lost during the migration.

## API Impact
The API responses remain backward compatible:
- Test endpoints still return `lesson_id` and `lesson_title` fields
- The fields are now computed using `SerializerMethodField` instead of direct field access
- All existing API consumers should continue to work without changes

## To Apply Changes
Run the following command to apply the migrations:
```bash
python manage.py migrate learning
```

## Rollback
If needed, you can rollback the changes:
```bash
python manage.py migrate learning 0008_question_video
```
