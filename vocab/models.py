from django.db import models

class WordList(models.Model):
    name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

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
    is_known = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ['-created_at']
