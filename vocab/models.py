from django.db import models
from django.utils import timezone
from datetime import timedelta


class WordList(models.Model):
    PROCESSING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # Background processing fields
    processing_status = models.CharField(
        max_length=20, choices=PROCESSING_STATUS_CHOICES, default="pending"
    )
    total_words = models.IntegerField(default=0)
    words_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def progress_percentage(self):
        """Calculate processing progress percentage"""
        if self.total_words == 0:
            return 0
        return int((self.words_processed / self.total_words) * 100)

    @property
    def is_processing(self):
        return self.processing_status in ["pending", "processing"]

    @property
    def is_reviewable(self):
        return (
            self.processing_status == "completed"
            and self.words.filter(is_known=False).exists()
        )

    class Meta:
        ordering = ["-created_at"]


class Vocabulary(models.Model):
    word_list = models.ForeignKey(
        WordList, on_delete=models.CASCADE, related_name="words", null=True
    )
    word = models.CharField(max_length=255)
    meaning_1 = models.TextField()
    meaning_2 = models.TextField(blank=True, null=True)
    meaning_3 = models.TextField(blank=True, null=True)
    is_known = models.BooleanField(default=False)

    # SRS Fields (SuperMemo-2 Algorithm)
    next_review_date = models.DateTimeField(null=True, blank=True)
    interval = models.IntegerField(default=0)  # Days until next review
    easiness_factor = models.FloatField(default=2.5)
    repetition_count = models.IntegerField(default=0)

    # Enhanced Content
    example_sentence = models.TextField(blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)

    level = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ["-created_at"]


class UserStats(models.Model):
    current_streak = models.IntegerField(default=0)
    last_review_date = models.DateField(null=True, blank=True)
    total_reviews = models.IntegerField(default=0)

    @classmethod
    def get_stats(cls):
        stats, created = cls.objects.get_or_create(id=1)
        return stats

    def update_streak(self):
        today = timezone.now().date()
        if self.last_review_date == today:
            return  # Already updated today

        if self.last_review_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1

        self.last_review_date = today
        self.total_reviews += 1
        self.save()
