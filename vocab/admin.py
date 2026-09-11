from django.contrib import admin

from .models import JoinedList, Vocabulary, WordList, WordProgress


@admin.register(WordList)
class WordListAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'share_code', 'created_at')
    search_fields = ('name', 'share_code', 'owner__username')


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('word', 'word_list')
    search_fields = ('word',)


@admin.register(WordProgress)
class WordProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'vocabulary', 'is_known', 'level', 'last_reviewed')
    list_filter = ('is_known',)


admin.site.register(JoinedList)
