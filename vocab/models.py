import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def generate_share_code():
    while True:
        code = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        if not WordList.objects.filter(share_code=code).exists():
            return code


class WordList(models.Model):
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_lists',
        null=True,
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=280, blank=True, default='')
    file_name = models.CharField(max_length=255)
    share_code = models.CharField(max_length=8, unique=True, db_index=True)
    is_public = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Background processing: words uploaded without meanings get filled in
    # from the dictionary API after the upload returns.
    processing_status = models.CharField(
        max_length=20, choices=PROCESSING_STATUS_CHOICES, default='completed'
    )
    total_words = models.IntegerField(default=0)
    words_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    @property
    def word_count(self):
        return self.words.count()

    @property
    def progress_percentage(self):
        """Share of words whose meanings have been fetched."""
        if self.total_words == 0:
            return 100
        return int((self.words_processed / self.total_words) * 100)

    @property
    def is_processing(self):
        return self.processing_status in ('pending', 'processing')

    def save(self, *args, **kwargs):
        if not self.share_code:
            self.share_code = generate_share_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Vocabulary(models.Model):
    word_list = models.ForeignKey(WordList, on_delete=models.CASCADE, related_name='words', null=True)
    word = models.CharField(max_length=255)
    meaning_1 = models.TextField()
    meaning_2 = models.TextField(blank=True, null=True)
    meaning_3 = models.TextField(blank=True, null=True)
    example_sentence = models.TextField(blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def meanings(self):
        return [m for m in (self.meaning_1, self.meaning_2, self.meaning_3) if m]

    def __str__(self):
        return self.word

    class Meta:
        ordering = ['-created_at']


class WordProgress(models.Model):
    """Per-user knowledge state for a word. Shared lists need one row per player."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='progress')
    is_known = models.BooleanField(default=False)
    level = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(blank=True, null=True)

    # Spaced repetition state (SuperMemo-2)
    next_review_date = models.DateTimeField(blank=True, null=True)
    interval = models.IntegerField(default=0)  # days until the next review
    easiness_factor = models.FloatField(default=2.5)
    repetition_count = models.IntegerField(default=0)

    def apply_review(self, is_known):
        """Update SM-2 scheduling for one answer. Right swipe = q4, left swipe = q0."""
        quality = 4 if is_known else 0

        if quality >= 3:
            if self.repetition_count == 0:
                self.interval = 1
            elif self.repetition_count == 1:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.easiness_factor)
            self.repetition_count += 1
            self.correct_count += 1
            self.level += 1
        else:
            self.repetition_count = 0
            self.interval = 1
            self.wrong_count += 1
            self.level = 0

        self.easiness_factor = max(
            1.3,
            self.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
        )
        self.is_known = is_known
        self.last_reviewed = timezone.now()
        self.next_review_date = self.last_reviewed + timedelta(days=self.interval)

    class Meta:
        unique_together = ('user', 'vocabulary')
        indexes = [models.Index(fields=['user', 'is_known'])]

    def __str__(self):
        return f'{self.user} / {self.vocabulary} / {"known" if self.is_known else "unknown"}'


class JoinedList(models.Model):
    """A list the user unlocked with a friend's share code."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='joined_lists')
    word_list = models.ForeignKey(WordList, on_delete=models.CASCADE, related_name='joined_by')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'word_list')
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.user} -> {self.word_list}'


class UserStats(models.Model):
    """Daily review streak, one row per user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stats')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_review_date = models.DateField(null=True, blank=True)
    total_reviews = models.IntegerField(default=0)

    @classmethod
    def get_stats(cls, user):
        stats, _ = cls.objects.get_or_create(user=user)
        return stats

    def update_streak(self):
        today = timezone.now().date()
        self.total_reviews += 1

        if self.last_review_date == today:
            self.save(update_fields=['total_reviews'])
            return

        if self.last_review_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1

        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_review_date = today
        self.save()

    def __str__(self):
        return f'{self.user} / streak {self.current_streak}'
