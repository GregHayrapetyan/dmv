from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Lesson(models.Model):
    """Single lesson (video, theory, etc.)."""

    class LessonType(models.TextChoices):
        VIDEO = "video", "Video"
        THEORY = "theory", "Theory"
        MIXED = "mixed", "Video + theory"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.VIDEO,
    )
    content = models.TextField(blank=True)  # text, description, extra notes
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order"
    )
    is_published = models.BooleanField(default=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated duration in minutes"
    )
    states = models.ManyToManyField(
        'onboarding.State',
        blank=True,
        related_name='lessons',
        help_text="States where this lesson is available. Leave empty for all states."
    )
    test = models.OneToOneField(
        'Test',
        on_delete=models.CASCADE,
        related_name='lesson',
        null=True,
        blank=True,
        help_text="Test associated with this lesson"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['slug']),
            models.Index(fields=['lesson_type']),
        ]

    def __str__(self):
        return self.title


class Test(models.Model):
    """
    Test for a specific lesson.
    One lesson has exactly one test.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="test_images/",
        blank=True,
        null=True,
        help_text="Cover image for the test",
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in seconds (if any)",
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Marks this test as a demo test",
    )
    passing_percentage = models.PositiveIntegerField(
        default=100,
        help_text="Percentage needed to pass (0-100)"
    )
    max_attempts = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum allowed attempts (null = unlimited)"
    )
    shuffle_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each attempt"
    )
    shuffle_answers = models.BooleanField(
        default=False,
        help_text="Randomize answer order for each attempt"
    )
    states = models.ManyToManyField(
        'onboarding.State',
        blank=True,
        related_name='tests',
        help_text="States where this test is available. Leave empty for all states."
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        indexes = [
            models.Index(fields=['is_demo']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(passing_percentage__gte=0, passing_percentage__lte=100),
                name='test_passing_percentage_range'
            ),
        ]

    def __str__(self):
        try:
            return f"Test for lesson: {self.lesson.title}"
        except:
            return f"Test: {self.title}"


class Question(models.Model):
    """Question inside a test."""

    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        TRUE_FALSE = "true_false", "True/False"

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
    video = models.FileField(
        upload_to="test_questions/videos/",
        blank=True,
        null=True,
        help_text="Video for the question (if any)",
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order of the question in the test",
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text="How many points this question is worth",
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["order", "id"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(points__gte=1),
                name='question_points_positive'
            ),
        ]

    def __str__(self):
        return f"Question #{self.order} for test '{self.test.title}'"

    def has_correct_answer(self):
        """Check if question has at least one correct answer."""
        return self.answer_options.filter(is_correct=True).exists()

    def validate_answers(self):
        """Validate that question has appropriate correct answers."""
        correct_count = self.answer_options.filter(is_correct=True).count()
        if correct_count == 0:
            raise ValidationError("Question must have at least one correct answer")
        if self.question_type == self.QuestionType.MULTIPLE_CHOICE and correct_count > 1:
            raise ValidationError("Multiple choice questions should have exactly one correct answer")
        if self.question_type == self.QuestionType.TRUE_FALSE:
            total_count = self.answer_options.count()
            if total_count != 2:
                raise ValidationError("True/False questions must have exactly 2 answer options")
            if correct_count != 1:
                raise ValidationError("True/False questions must have exactly one correct answer")


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
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Answer option"
        verbose_name_plural = "Answer options"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'order'],
                name='unique_answer_order_per_question'
            ),
        ]

    def __str__(self):
        prefix = "✓" if self.is_correct else "✗"
        return f"{prefix} Answer #{self.order} for question {self.question_id}"


class LessonProgress(models.Model):
    """Track user progress through lessons."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lesson progress"
        verbose_name_plural = "Lesson progress"
        unique_together = ['user', 'lesson']
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['lesson', 'completed']),
        ]

    def __str__(self):
        status = "Completed" if self.completed else "In Progress"
        return f"{self.user.email} - {self.lesson.title} ({status})"


class TestAttempt(models.Model):
    """Record of a user's test attempt."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    score = models.PositiveIntegerField()
    total_points = models.PositiveIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField()
    time_taken_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time taken to complete the test in seconds"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Test attempt"
        verbose_name_plural = "Test attempts"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'test', '-started_at']),
            models.Index(fields=['user', 'passed']),
            models.Index(fields=['test', '-started_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.test.title} - {self.percentage}% ({self.started_at.strftime('%Y-%m-%d')})"


class TestAnswer(models.Model):
    """Individual answer within a test attempt."""

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_option = models.ForeignKey(
        AnswerOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The answer option selected by the user (null if skipped)"
    )
    is_correct = models.BooleanField()

    class Meta:
        verbose_name = "Test answer"
        verbose_name_plural = "Test answers"
        unique_together = ['attempt', 'question']
        indexes = [
            models.Index(fields=['attempt', 'is_correct']),
        ]

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"Answer for Q{self.question.order} - {status}"


class FavoriteLesson(models.Model):
    """Track user's favorite lessons."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_lessons'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favorite lesson"
        verbose_name_plural = "Favorite lessons"
        unique_together = ['user', 'lesson']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['lesson']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.lesson.title}"
