import secrets

from django.conf import settings
from django.db import models

CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def generate_share_code():
    while True:
        code = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        if not WordList.objects.filter(share_code=code).exists():
            return code


class WordList(models.Model):
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

    @property
    def word_count(self):
        return self.words.count()

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
