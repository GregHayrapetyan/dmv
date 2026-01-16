# Wagtail CMS - Quick Start Guide

## What Was Done

✅ Installed Wagtail CMS and dependencies
✅ Updated Django settings with Wagtail configuration
✅ Created CMS app with 5 page types
✅ Configured URL routing
✅ Ran all migrations
✅ Set up Wagtail API endpoints
✅ Integrated Learning System models into Wagtail admin
✅ Integrated Site Details models into Wagtail admin

## Quick Start

### 1. Start the Development Server

```bash
python manage.py runserver
```

### 2. Access Wagtail Admin

Open your browser and go to:
```
http://localhost:8000/cms/
```

Login with your Django superuser credentials.

### 3. Create Your First Page

1. Click on "Pages" in the left sidebar
2. Click "Add child page" under the root
3. Choose "Home Page"
4. Fill in:
   - Title: "Home"
   - Banner Title: "Welcome to MyTest DMV"
   - Banner Subtitle: "Master Your DMV Test"
   - Intro: Add some welcome text
5. Click "Publish"

### 4. Set as Root Page

1. Go to Settings → Sites (in the left sidebar)
2. Click on "localhost"
3. Set:
   - Hostname: `localhost`
   - Port: `8000`
   - Root page: Select your newly created "Home" page
4. Save

### 5. Create More Pages

Add child pages to your HomePage:

**About Page:**
- Type: Standard Page
- Title: "About Us"
- Add content using the StreamField blocks

**Blog:**
- Type: Blog Index Page
- Title: "Blog"
- Then add Blog Page entries as children

**FAQ:**
- Type: FAQ Page
- Title: "Frequently Asked Questions"

### 6. Manage Learning Content

All your existing models are now in Wagtail admin:

**Learning System:**
- Lessons, Tests, Questions, Answer Options
- Lesson Progress, Test Attempts
- Favorite Lessons

**Site Details:**
- Pricing Plans, Plan Features
- Client Reviews, Contact Messages
- Contact Information, Partners

See [WAGTAIL_MODELADMIN_INTEGRATION.md](WAGTAIL_MODELADMIN_INTEGRATION.md) for details.

## Available Endpoints

### Admin Interfaces
- **Wagtail CMS Admin**: http://localhost:8000/cms/
- **Django Admin**: http://localhost:8000/admin/

### API Endpoints
- **Wagtail Pages API**: http://localhost:8000/api/cms/v2/pages/
- **Wagtail Images API**: http://localhost:8000/api/cms/v2/images/
- **Wagtail Documents API**: http://localhost:8000/api/cms/v2/documents/
- **Your Learning API**: http://localhost:8000/api/learning/
- **API Documentation**: http://localhost:8000/api/docs/

## Content Management

### CMS Page Types

1. **HomePage** - Main landing page with banner
2. **StandardPage** - Generic content pages (About, Contact, etc.)
3. **BlogIndexPage** - Blog listing page
4. **BlogPage** - Individual blog posts
5. **FAQPage** - FAQ pages

### Learning System (ModelAdmin)

- **Lesson Categories** - Organize lessons
- **Lessons** - Video and theory content
- **Tests** - Exam management
- **Questions & Answers** - Test content
- **Progress Tracking** - User progress and attempts

### Site Details (ModelAdmin)

- **Pricing Plans** - Subscription management
- **Client Reviews** - Testimonials
- **Contact** - Messages and info
- **Partners** - Partner/sponsor management

## Next Steps

1. ✅ Create your initial page structure
2. ✅ Customize page content
3. 📝 Create custom templates (optional)
4. 📝 Add more content blocks (optional)
5. 📝 Set up user permissions for content editors
6. 📝 Integrate with your frontend

## File Structure

```
dmv/
├── cms/                      # New CMS app
│   ├── models.py            # Page models
│   ├── api.py               # API configuration
│   └── migrations/          # Database migrations
├── dmv/
│   ├── settings.py          # Updated with Wagtail config
│   └── urls.py              # Updated with Wagtail URLs
├── requirements.txt         # Updated with Wagtail
├── WAGTAIL_INTEGRATION.md   # Full documentation
└── WAGTAIL_QUICKSTART.md    # This file
```

## Useful Commands

```bash
# Create a new superuser
python manage.py createsuperuser

# Make migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Collect static files (for production)
python manage.py collectstatic

# Create a new page type
# Edit cms/models.py, then run:
python manage.py makemigrations cms
python manage.py migrate cms
```

## Tips

- **Drafts**: Pages can be saved as drafts before publishing
- **Revisions**: Wagtail keeps a history of all changes
- **Preview**: Use the preview button to see pages before publishing
- **Search**: Wagtail has built-in search functionality
- **Permissions**: Set up groups to control who can edit what

## Need Help?

- See `WAGTAIL_INTEGRATION.md` for detailed documentation
- Visit https://docs.wagtail.org/ for official Wagtail docs
- Check the Wagtail admin interface - it's very intuitive!

## Example API Usage

```bash
# Get all pages
curl http://localhost:8000/api/cms/v2/pages/

# Get a specific page
curl http://localhost:8000/api/cms/v2/pages/2/

# Get page with full details
curl http://localhost:8000/api/cms/v2/pages/2/?fields=*
```

---

**Ready to go!** Start by accessing http://localhost:8000/cms/ and creating your first page.
