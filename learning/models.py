from django.db import models


class LessonCategory(models.Model):
    """Category of driving lessons (e.g. 'Road signs')."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Lesson category"
        verbose_name_plural = "Lesson categories"

    def __str__(self):
        return self.name


class Lesson(models.Model):
    """Single lesson (video, theory, etc.)."""

    class LessonType(models.TextChoices):
        VIDEO = "video", "Video"
        THEORY = "theory", "Theory"
        MIXED = "mixed", "Video + theory"

    category = models.ForeignKey(
        LessonCategory,
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.VIDEO,
    )
    content = models.TextField(blank=True)  # text, description, extra notes
    video_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"

    def __str__(self):
        return self.title


class TestCategory(models.Model):
    """
    Category of tests that matches a lesson category.
    For example: 'Tests for road signs'.
    """

    lesson_category = models.OneToOneField(
        LessonCategory,
        on_delete=models.CASCADE,
        related_name="test_category",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Test category"
        verbose_name_plural = "Test categories"

    def __str__(self):
        return self.name


class Test(models.Model):
    """
    Test for a specific lesson.
    One lesson has exactly one test,
    and the test belongs to the corresponding test category.
    """

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name="test",
    )
    test_category = models.ForeignKey(
        TestCategory,
        on_delete=models.PROTECT,
        related_name="tests",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in seconds (if any)",
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Marks this test as a demo test",
    )

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"

    def save(self, *args, **kwargs):
        # Automatically set test_category from the lesson category if not provided
        if self.lesson and not self.test_category_id:
            if hasattr(self.lesson.category, "test_category"):
                self.test_category = self.lesson.category.test_category
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Test for lesson: {self.lesson.title}"


class Question(models.Model):
    """Question inside a test."""

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    image = models.ImageField(
        upload_to="test_questions/",
        blank=True,
        null=True,
        help_text="Image for the question (if any)",
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order of the question in the test",
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text="How many points this question is worth",
    )

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["order", "id"]

    def __str__(self):
        return f"Question #{self.order} for test '{self.test.title}'"


class AnswerOption(models.Model):
    """Single answer option for a question."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answer_options",
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(
        blank=True,
        help_text="Explanation for why this option is correct/incorrect "
                  "(can be shown after answering)",
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order of the answer option",
    )

    class Meta:
        verbose_name = "Answer option"
        verbose_name_plural = "Answer options"
        ordering = ["order", "id"]

    def __str__(self):
        prefix = "✓" if self.is_correct else "✗"
        return f"{prefix} Answer #{self.order} for question {self.question_id}"
