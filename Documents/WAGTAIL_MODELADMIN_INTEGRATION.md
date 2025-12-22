# Wagtail ModelAdmin Integration

This document describes how the Learning System and Site Details models are integrated into the Wagtail CMS admin interface.

## Overview

All your existing Django models are now accessible through the Wagtail admin interface at `http://localhost:8000/cms/`. This provides a unified, modern admin interface for managing all content.

## What's Integrated

### Learning System Models

Access via **Learning System** menu group in Wagtail admin:

1. **Lesson Categories** - Organize lessons into categories
2. **Lessons** - Manage lesson content, videos, and materials
3. **Tests** - Create and manage tests
4. **Questions** - Add questions to tests
5. **Answer Options** - Define answer choices for questions
6. **Lesson Progress** - Track user progress through lessons
7. **Test Attempts** - View user test submissions
8. **Favorite Lessons** - See which lessons users have favorited

### Site Details Models

Access via **Site Details** menu group in Wagtail admin:

1. **Pricing Plans** - Manage subscription plans and pricing
2. **Plan Features** - Define features for each pricing plan
3. **Client Reviews** - Manage customer testimonials
4. **Contact Information** - Update business contact details
5. **Contact Messages** - View and respond to contact form submissions
6. **Partners** - Manage partner/sponsor information

## Benefits of Wagtail Admin

### Compared to Django Admin

✅ **Modern UI** - Clean, intuitive interface
✅ **Better UX** - Easier navigation and content management
✅ **Unified Interface** - All content in one place
✅ **Rich Editing** - Better forms and editing experience
✅ **Permissions** - Granular permission control
✅ **Search** - Better search and filtering
✅ **Mobile Friendly** - Responsive design

### Features

- **List Views** - See all records with customizable columns
- **Filtering** - Filter by various fields
- **Search** - Full-text search across models
- **Bulk Actions** - Perform actions on multiple items
- **Inline Editing** - Edit related records inline
- **Custom Ordering** - Drag-and-drop ordering where applicable

## Accessing the Admin

### URL
```
http://localhost:8000/cms/
```

### Login
Use your Django superuser credentials.

### Navigation

1. **Dashboard** - Overview and quick links
2. **Pages** - Wagtail CMS pages (Blog, About, etc.)
3. **Learning System** - All learning-related models
4. **Site Details** - All site configuration models
5. **Images** - Media library
6. **Documents** - Document library
7. **Settings** - Site settings

## Common Tasks

### Managing Lessons

1. Go to **Learning System** → **Lessons**
2. Click **Add Lesson** to create new
3. Fill in:
   - Title
   - Category
   - Content
   - Upload video (duration auto-calculated)
   - Upload image
   - Set order
   - Select states (if state-specific)
   - Link to test
4. Click **Save**

### Managing Tests

1. Go to **Learning System** → **Tests**
2. Click **Add Test**
3. Configure:
   - Title and description
   - Time limit
   - Passing percentage
   - Demo test flag
   - Shuffle options
4. Add questions via **Questions** menu
5. Add answer options via **Answer Options** menu

### Managing Reviews

1. Go to **Site Details** → **Client Reviews**
2. Click **Add Client Review**
3. Upload avatar
4. Enter name, job title
5. Set rating (1-5 stars)
6. Write review text
7. Set display order
8. Mark as active
9. Click **Save**

### Managing Contact Information

1. Go to **Site Details** → **Contact Information**
2. Edit existing or add new
3. Update:
   - Address lines
   - Phone numbers
   - Email addresses
4. Only one can be active at a time (singleton pattern)
5. Click **Save**

### Viewing Contact Messages

1. Go to **Site Details** → **Contact Messages**
2. View all submissions
3. Filter by status (New, In Progress, Resolved)
4. Click on a message to view details
5. Update status as needed

### Managing Pricing Plans

1. Go to **Site Details** → **Pricing Plans**
2. Click **Add Pricing Plan**
3. Configure:
   - Title and subtitle
   - Pricing (old price, new price, discount)
   - Button text and URL
   - Stripe integration IDs
   - Featured flag
   - Display order
4. Add features via **Plan Features** menu
5. Click **Save**

## User Progress Tracking

### Lesson Progress

View user progress through lessons:
- **Learning System** → **Lesson Progress**
- See which users completed which lessons
- Track completion dates
- Filter by completion status

### Test Attempts

Monitor test performance:
- **Learning System** → **Test Attempts**
- View all test submissions
- See scores and pass/fail status
- Filter by user or test
- Track time taken

## Permissions

### Setting Up Content Editors

1. Go to **Settings** → **Users**
2. Click **Add a user**
3. Set username and password
4. Assign to groups:
   - **Editors** - Can edit content
   - **Moderators** - Can publish content
5. Set specific permissions per model

### Permission Levels

- **View** - Can see records
- **Add** - Can create new records
- **Edit** - Can modify existing records
- **Delete** - Can remove records
- **Publish** - Can publish pages (for CMS pages)

## Customization

### Adding New Models

To add more Django models to Wagtail admin:

1. Edit `/home/greg/dmv/cms/wagtail_hooks.py`
2. Import your model
3. Create a ModelAdmin class:

```python
from myapp.models import MyModel

class MyModelAdmin(ModelAdmin):
    model = MyModel
    menu_label = 'My Models'
    menu_icon = 'doc-full'
    list_display = ('field1', 'field2', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'description')
```

4. Add to a group or register individually:

```python
# Add to existing group
class MyGroup(ModelAdminGroup):
    items = (MyModelAdmin, OtherAdmin)

# Or register individually
modeladmin_register(MyModelAdmin)
```

### Customizing List Views

Edit the `list_display` tuple in ModelAdmin classes:

```python
class LessonAdmin(ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_published')
```

### Adding Filters

Edit the `list_filter` tuple:

```python
class TestAdmin(ModelAdmin):
    list_filter = ('is_demo', 'states', 'vehicles')
```

### Custom Search

Edit the `search_fields` tuple:

```python
class QuestionAdmin(ModelAdmin):
    search_fields = ('text', 'test__title')
```

## Tips & Best Practices

### Content Management

1. **Use Ordering** - Set `order` fields to control display sequence
2. **Mark as Active** - Use `is_active` flags to hide/show content
3. **Regular Backups** - Back up your database regularly
4. **Test Changes** - Use draft/preview features before publishing

### Performance

1. **Optimize Images** - Compress images before uploading
2. **Limit List Display** - Don't show too many fields in list views
3. **Use Filters** - Add filters for large datasets
4. **Index Fields** - Ensure database indexes on filtered/searched fields

### Security

1. **Strong Passwords** - Use strong passwords for admin users
2. **Limited Access** - Only give admin access to trusted users
3. **Audit Logs** - Review Wagtail's built-in audit logs
4. **HTTPS** - Always use HTTPS in production

## Troubleshooting

### Can't See Models in Admin

**Problem:** Models don't appear in Wagtail admin menu

**Solution:**
1. Check that `wagtail_modeladmin` is in `INSTALLED_APPS`
2. Verify `wagtail_hooks.py` is in the `cms` app
3. Ensure ModelAdmin classes are registered
4. Restart the development server

### Permission Denied

**Problem:** User can't access certain models

**Solution:**
1. Check user permissions in Settings → Users
2. Assign appropriate groups
3. Verify model permissions are set correctly

### Changes Not Showing

**Problem:** Updates don't appear on the site

**Solution:**
1. Check if content is published (not draft)
2. Clear browser cache
3. Restart development server
4. Check `is_active` flags

## API Access

All models are still accessible via your existing REST API:

- **Learning API**: `http://localhost:8000/api/learning/`
- **Site Details API**: `http://localhost:8000/api/site-details/`
- **Wagtail API**: `http://localhost:8000/api/cms/v2/`

The Wagtail admin is just an alternative interface - your API remains unchanged.

## Migration from Django Admin

### What Changed

- ✅ All functionality preserved
- ✅ Better UI/UX
- ✅ Additional features (search, filters, etc.)
- ✅ Same data, different interface

### What Stayed the Same

- ✅ Database structure unchanged
- ✅ API endpoints unchanged
- ✅ Models unchanged
- ✅ Permissions system compatible

### Django Admin Still Available

The Django admin is still accessible at:
```
http://localhost:8000/admin/
```

You can use both interfaces simultaneously if needed.

## Next Steps

1. ✅ Explore the Wagtail admin interface
2. ✅ Create some test content
3. ✅ Set up user permissions
4. ✅ Train content editors
5. ✅ Customize as needed

## Resources

- [Wagtail ModelAdmin Documentation](https://github.com/wagtail/wagtail-modeladmin)
- [Wagtail Documentation](https://docs.wagtail.org/)
- [Django Admin vs Wagtail](https://docs.wagtail.org/en/stable/getting_started/tutorial.html)

---

**Ready to use!** Access the Wagtail admin at http://localhost:8000/cms/
