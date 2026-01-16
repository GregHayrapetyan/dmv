# Wagtail CMS Integration

This document describes the Wagtail CMS integration in the DMV Test Preparation project.

## Overview

Wagtail has been integrated to manage content pages, blog posts, and other marketing/informational content separately from the API-based learning system.

## Access Points

- **Wagtail Admin**: http://localhost:8000/cms/
- **Django Admin**: http://localhost:8000/admin/
- **Wagtail API**: http://localhost:8000/api/cms/v2/pages/
- **Your existing API**: http://localhost:8000/api/

## Page Types

### 1. HomePage
The main landing page for your site.

**Fields:**
- `banner_title` - Main banner title
- `banner_subtitle` - Banner subtitle text
- `intro` - Rich text introduction

**Usage:** Create one HomePage as the root of your site tree.

### 2. StandardPage
Generic content pages for About, Contact, Privacy Policy, Terms of Service, etc.

**Fields:**
- `intro` - Brief introduction or summary
- `body` - StreamField with flexible content blocks (headings, paragraphs, images)

**Usage:** Create as many as needed for static content pages.

### 3. BlogIndexPage
Blog listing page that displays all blog posts.

**Fields:**
- `intro` - Rich text introduction for the blog

**Usage:** Create one BlogIndexPage, then add BlogPage entries as children.

### 4. BlogPage
Individual blog posts.

**Fields:**
- `date` - Publication date
- `intro` - Brief excerpt
- `body` - StreamField with flexible content blocks

**Usage:** Create as children of BlogIndexPage. Great for DMV tips, driving advice, state updates.

### 5. FAQPage
FAQ page for frequently asked questions.

**Fields:**
- `intro` - Rich text introduction

**Usage:** Create FAQ pages for common questions about DMV tests.

## Getting Started

### 1. Create Initial Site Structure

After running migrations, you need to create your first pages:

```bash
# Access Wagtail admin
http://localhost:8000/cms/

# Login with your Django superuser credentials
```

### 2. Create a HomePage

1. In Wagtail admin, go to Pages
2. Click "Add child page" under "Welcome to your new Wagtail site!"
3. Choose "Home Page"
4. Fill in the banner title, subtitle, and intro
5. Publish the page

### 3. Set as Root Page

1. Go to Settings → Sites
2. Edit the default site
3. Set the HomePage as the root page
4. Set hostname to `localhost` (or your domain)
5. Set port to `8000` (or your port)
6. Save

### 4. Create Additional Pages

You can now add child pages to your HomePage:
- StandardPage for About, Contact, etc.
- BlogIndexPage for your blog
- FAQPage for frequently asked questions

## Content Blocks

All page types use StreamField with these content blocks:

- **Heading** - Section headings
- **Paragraph** - Rich text paragraphs
- **Image** - Images from the media library

You can add, remove, and reorder these blocks to create flexible page layouts.

## API Access

Wagtail pages are available via REST API:

```bash
# List all pages
GET http://localhost:8000/api/cms/v2/pages/

# Get specific page
GET http://localhost:8000/api/cms/v2/pages/{id}/

# List images
GET http://localhost:8000/api/cms/v2/images/

# List documents
GET http://localhost:8000/api/cms/v2/documents/
```

## Use Cases

### Marketing Content
- About Us
- Contact Information
- Privacy Policy
- Terms of Service
- Pricing Information

### Blog
- DMV test tips
- Driving advice
- State-specific updates
- New feature announcements

### Help & Support
- FAQ pages
- How-to guides
- Troubleshooting

### State-Specific Content
Create custom landing pages for different states with relevant information.

## Integration with Existing Models

You can reference your existing Django models in Wagtail pages. For example:

```python
from learning.models import LessonCategory

class LessonCategoryPage(Page):
    category = models.ForeignKey(
        LessonCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+'
    )
    
    def get_context(self, request):
        context = super().get_context(request)
        if self.category:
            context['lessons'] = self.category.lessons.filter(is_published=True)
        return context
```

## Customization

### Adding New Page Types

1. Edit `/home/greg/dmv/cms/models.py`
2. Create a new class inheriting from `Page`
3. Add fields and content panels
4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Adding New Content Blocks

Edit the `ContentBlock` class in `cms/models.py`:

```python
class ContentBlock(StreamBlock):
    heading = CharBlock(classname="full title", icon="title")
    paragraph = RichTextBlock(icon="pilcrow")
    image = ImageChooserBlock(icon="image")
    # Add new blocks here
    video = EmbedBlock(icon="media")
    quote = BlockQuoteBlock()
```

## Templates

Wagtail uses Django templates. Create custom templates in:

```
cms/templates/cms/
├── home_page.html
├── standard_page.html
├── blog_index_page.html
├── blog_page.html
└── faq_page.html
```

Default templates are provided by Wagtail if you don't create custom ones.

## Best Practices

1. **Separation of Concerns**: Use Wagtail for marketing/content pages, keep your API for the learning system
2. **SEO**: Wagtail provides built-in SEO fields (meta description, search image, etc.)
3. **Drafts**: Use Wagtail's draft/publish workflow for content review
4. **Permissions**: Set up user groups with appropriate permissions for content editors
5. **Backups**: Wagtail content is stored in your PostgreSQL database, so regular backups are essential

## Troubleshooting

### Can't access Wagtail admin
- Make sure you've created a superuser: `python manage.py createsuperuser`
- Check that Wagtail is in INSTALLED_APPS
- Verify the URL is correct: http://localhost:8000/cms/

### Pages not showing
- Check that pages are published (not in draft)
- Verify the site settings point to the correct root page
- Check URL routing in `dmv/urls.py`

### API not working
- Ensure `wagtail.api.v2` is in INSTALLED_APPS
- Check that `api_router.urls` is included in `dmv/urls.py`
- Verify the API endpoint: http://localhost:8000/api/cms/v2/pages/

## Resources

- [Wagtail Documentation](https://docs.wagtail.org/)
- [Wagtail Tutorial](https://docs.wagtail.org/en/stable/getting_started/tutorial.html)
- [StreamField Guide](https://docs.wagtail.org/en/stable/topics/streamfield.html)
- [Wagtail API](https://docs.wagtail.org/en/stable/advanced_topics/api/index.html)

## Next Steps

1. Create your initial page structure in Wagtail admin
2. Customize page templates to match your design
3. Add more content blocks as needed
4. Set up user permissions for content editors
5. Consider adding Wagtail extensions:
   - wagtail-seo for advanced SEO
   - wagtail-cache for performance
   - wagtail-localize for multi-language support
