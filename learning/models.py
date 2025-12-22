from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os


class LessonCategory(models.Model):
    """Category for organizing lessons."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Lesson Category"
        verbose_name_plural = "Lesson Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


def validate_lesson_image_dimensions(image):
    """Validate that lesson image is at least 800x500 pixels."""
    if image:
        img = Image.open(image)
        width, height = img.size
        
        if width < 800 or height < 500:
            raise ValidationError(
                f'Image dimensions must be at least 800x500 pixels. '
                f'Uploaded image is {width}x{height} pixels.'
            )


class Lesson(models.Model):
    """Single lesson (video, theory, etc.)."""
    # add seconds duration
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        LessonCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        help_text="Category for this lesson"
    )
    content = models.TextField(blank=True)  # text, description, extra notes
    video = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    image = models.ImageField(
        upload_to='lessons/images/',
        blank=True,
        null=True,
        validators=[validate_lesson_image_dimensions],
        help_text="Image must be at least 800x500 pixels"
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order"
    )
    is_published = models.BooleanField(default=True)
    duration_minutes = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Duration in minutes (auto-calculated from video if available)"
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
        ]

    def __str__(self):
        return self.title
    
    def get_video_duration(self):
        """Extract video duration in seconds using moviepy."""
        if not self.video:
            return None
        
        try:
            from moviepy.editor import VideoFileClip
            
            # Open video file and get duration
            with VideoFileClip(self.video.path) as clip:
                duration_seconds = clip.duration
                return duration_seconds
        except (ImportError, Exception):
            # If moviepy is not installed or fails, return None
            pass
        
        return None
    
    def save(self, *args, **kwargs):
        """Track if video has changed before saving."""
        # Store whether video changed for use in post_save signal
        if self.pk:
            try:
                old_instance = Lesson.objects.get(pk=self.pk)
                self._video_changed = old_instance.video != self.video
            except Lesson.DoesNotExist:
                self._video_changed = True
        else:
            self._video_changed = bool(self.video)
        
        super().save(*args, **kwargs)


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
    #TODO add video upload
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
    vehicles = models.ManyToManyField(
        'onboarding.Vehicle',
        blank=True,
        related_name='tests',
        help_text="Vehicle types for this test. Leave empty for all vehicle types."
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
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["order", "id"]

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
    correct_answers = models.PositiveIntegerField()
    incorrect_answers = models.PositiveIntegerField()
    questions_count = models.PositiveIntegerField()
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


@receiver(post_save, sender=Lesson)
def update_lesson_duration(sender, instance, created, **kwargs):
    """
    Signal to automatically update lesson duration after video is saved.
    This runs after the file is saved to disk, so we can read it.
    """
    # Check if video changed (tracked in save method)
    if hasattr(instance, '_video_changed') and instance._video_changed and instance.video:
        # Get video duration
        duration_seconds = instance.get_video_duration()
        
        if duration_seconds:
            # Convert to minutes with exact decimal (2 decimal places)
            duration_minutes = round(duration_seconds / 60, 2)
            
            # Only update if different to avoid infinite loop
            if instance.duration_minutes != duration_minutes:
                # Use update to avoid triggering save again
                Lesson.objects.filter(pk=instance.pk).update(duration_minutes=duration_minutes)
