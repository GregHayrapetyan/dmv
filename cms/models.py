from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import CharBlock, RichTextBlock, StreamBlock, StructBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.api import APIField
from wagtail.search import index


class ContentBlock(StreamBlock):
    """Reusable content blocks for flexible page content."""
    heading = CharBlock(classname="full title", icon="title")
    paragraph = RichTextBlock(icon="pilcrow")
    image = ImageChooserBlock(icon="image")


class HomePage(Page):
    """Homepage for the DMV site."""
    
    banner_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Main banner title"
    )
    banner_subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Banner subtitle text"
    )
    intro = RichTextField(
        blank=True,
        help_text="Introduction text for the homepage"
    )
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('banner_title'),
            FieldPanel('banner_subtitle'),
        ], heading="Banner Section"),
        FieldPanel('intro'),
    ]
    
    api_fields = [
        APIField('banner_title'),
        APIField('banner_subtitle'),
        APIField('intro'),
    ]
    
    class Meta:
        verbose_name = "Home Page"


class StandardPage(Page):
    """Generic content page (About, FAQ, Contact, etc.)."""
    
    intro = models.CharField(
        max_length=250,
        blank=True,
        help_text="Brief introduction or summary"
    )
    body = StreamField(
        ContentBlock(),
        use_json_field=True,
        blank=True,
        help_text="Main page content"
    )
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
    ]
    
    api_fields = [
        APIField('intro'),
        APIField('body'),
    ]
    
    class Meta:
        verbose_name = "Standard Page"


class BlogIndexPage(Page):
    """Blog listing page."""
    
    intro = RichTextField(
        blank=True,
        help_text="Introduction text for the blog"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    def get_context(self, request):
        """Add blog posts to context."""
        context = super().get_context(request)
        # Get all live blog posts, ordered by most recent
        context['posts'] = BlogPage.objects.live().public().order_by('-first_published_at')
        return context
    
    api_fields = [
        APIField('intro'),
    ]
    
    class Meta:
        verbose_name = "Blog Index Page"
    
    # Only allow BlogPage as children
    subpage_types = ['cms.BlogPage']


class BlogPage(Page):
    """Individual blog post."""
    
    date = models.DateField(
        "Post date",
        help_text="Publication date for this blog post"
    )
    intro = models.CharField(
        max_length=250,
        help_text="Brief introduction or excerpt"
    )
    body = StreamField(
        ContentBlock(),
        use_json_field=True,
        help_text="Main blog post content"
    )
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
    ]
    
    api_fields = [
        APIField('date'),
        APIField('intro'),
        APIField('body'),
    ]
    
    class Meta:
        verbose_name = "Blog Page"
    
    # Don't allow any children
    subpage_types = []
    
    # Only allow this page type under BlogIndexPage
    parent_page_types = ['cms.BlogIndexPage']


class FAQPage(Page):
    """FAQ page with questions and answers."""
    
    intro = RichTextField(
        blank=True,
        help_text="Introduction text for the FAQ page"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    api_fields = [
        APIField('intro'),
    ]
    
    class Meta:
        verbose_name = "FAQ Page"
