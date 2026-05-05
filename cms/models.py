from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.blocks import CharBlock, RichTextBlock, StreamBlock, StructBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.api import APIField
from wagtail.search import index
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel


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


# Test Management Models

class CMSTest(ClusterableModel):
    """Test snippet for Wagtail CMS with inline questions and answers."""
    
    title = models.CharField(max_length=255, help_text="English title")
    description = models.TextField(blank=True, help_text="English description")
    
    # Multilingual fields - Russian
    title_ru = models.CharField(max_length=255, blank=True, verbose_name="Title (Russian)")
    description_ru = models.TextField(blank=True, verbose_name="Description (Russian)")
    
    # Multilingual fields - Armenian
    title_hy = models.CharField(max_length=255, blank=True, verbose_name="Title (Armenian)")
    description_hy = models.TextField(blank=True, verbose_name="Description (Armenian)")
    
    # Multilingual fields - Hindi
    title_hi = models.CharField(max_length=255, blank=True, verbose_name="Title (Hindi)")
    description_hi = models.TextField(blank=True, verbose_name="Description (Hindi)")
    
    # Multilingual fields - Spanish
    title_es = models.CharField(max_length=255, blank=True, verbose_name="Title (Spanish)")
    description_es = models.TextField(blank=True, verbose_name="Description (Spanish)")
    
    # Multilingual fields - Chinese
    title_zh = models.CharField(max_length=255, blank=True, verbose_name="Title (Chinese)")
    description_zh = models.TextField(blank=True, verbose_name="Description (Chinese)")
    
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    passing_percentage = models.PositiveIntegerField(
        default=100,
        help_text="Percentage needed to pass (0-100)"
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in seconds (leave empty for no limit)"
    )
    max_attempts = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum allowed attempts (leave empty for unlimited)"
    )
    shuffle_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each attempt"
    )
    shuffle_answers = models.BooleanField(
        default=False,
        help_text="Randomize answer order for each attempt"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (drag to reorder)"
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Whether this test is a demo test (accessible without subscription)"
    )
    mixed_question_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of random questions to pull from this test for the mixed screening test. Set 0 to exclude."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ['order', 'id']


class CMSQuestion(ClusterableModel):
    """Question within a test."""
    
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    test = ParentalKey(
        CMSTest,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    text = models.TextField(help_text="Question text (English)")
    
    # Multilingual fields - Russian
    text_ru = models.TextField(blank=True, verbose_name="Text (Russian)")
    explanation_ru = models.TextField(blank=True, verbose_name="Explanation (Russian)")
    
    # Multilingual fields - Armenian
    text_hy = models.TextField(blank=True, verbose_name="Text (Armenian)")
    explanation_hy = models.TextField(blank=True, verbose_name="Explanation (Armenian)")
    
    # Multilingual fields - Hindi
    text_hi = models.TextField(blank=True, verbose_name="Text (Hindi)")
    explanation_hi = models.TextField(blank=True, verbose_name="Explanation (Hindi)")
    
    # Multilingual fields - Spanish
    text_es = models.TextField(blank=True, verbose_name="Text (Spanish)")
    explanation_es = models.TextField(blank=True, verbose_name="Explanation (Spanish)")
    
    # Multilingual fields - Chinese
    text_zh = models.TextField(blank=True, verbose_name="Text (Chinese)")
    explanation_zh = models.TextField(blank=True, verbose_name="Explanation (Chinese)")
    
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Optional image for the question"
    )
    video = models.FileField(
        upload_to="test_questions/videos/",
        blank=True,
        null=True,
        help_text="Video for the question (if any)",
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='multiple_choice'
    )
    explanation = models.TextField(
        blank=True,
        help_text="Explanation for the correct answer (English)"
    )
    
    panels = [
        FieldPanel('image'),
        FieldPanel('video'),
        FieldPanel('question_type'),
        FieldPanel('order'),
        FieldPanel('text'),
        FieldPanel('explanation'),
        FieldPanel('text_ru'),
        FieldPanel('explanation_ru'),
        FieldPanel('text_hy'),
        FieldPanel('explanation_hy'),
        FieldPanel('text_hi'),
        FieldPanel('explanation_hi'),
        FieldPanel('text_es'),
        FieldPanel('explanation_es'),
        FieldPanel('text_zh'),
        FieldPanel('explanation_zh'),
        InlinePanel('answers', label="Answer Options"),
    ]
    
    def __str__(self):
        return f"Question: {self.text[:50]}"
    
    class Meta:
        ordering = ('order',)
        verbose_name = "Question"
        verbose_name_plural = "Questions"


class CMSAnswer(models.Model):
    """Answer option for a question."""
    
    question = ParentalKey(
        CMSQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    text = models.TextField(help_text="Answer text (English)")
    
    # Multilingual fields - Russian
    text_ru = models.TextField(blank=True, verbose_name="Text (Russian)")
    
    # Multilingual fields - Armenian
    text_hy = models.TextField(blank=True, verbose_name="Text (Armenian)")
    
    # Multilingual fields - Hindi
    text_hi = models.TextField(blank=True, verbose_name="Text (Hindi)")
    
    # Multilingual fields - Spanish
    text_es = models.TextField(blank=True, verbose_name="Text (Spanish)")
    
    # Multilingual fields - Chinese
    text_zh = models.TextField(blank=True, verbose_name="Text (Chinese)")
    
    is_correct = models.BooleanField(
        default=False,
        help_text="Check if this is the correct answer"
    )
    
    panels = [
        FieldPanel('order'),
        FieldPanel('is_correct'),
        FieldPanel('text'),
        FieldPanel('text_ru'),
        FieldPanel('text_hy'),
        FieldPanel('text_hi'),
        FieldPanel('text_es'),
        FieldPanel('text_zh'),
    ]
    
    def __str__(self):
        prefix = "✓" if self.is_correct else "✗"
        return f"{prefix} {self.text[:50]}"
    
    class Meta:
        ordering = ('order',)
        verbose_name = "Answer Option"
        verbose_name_plural = "Answer Options"
