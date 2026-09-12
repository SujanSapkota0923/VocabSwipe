from django.contrib import admin

from .models import JoinedList, UserStats, Vocabulary, WordList, WordProgress


@admin.register(WordList)
class WordListAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'share_code', 'is_public', 'processing_status', 'created_at')
    list_filter = ('is_public', 'processing_status')
    search_fields = ('name', 'share_code', 'owner__username')


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('word', 'word_list')
    search_fields = ('word',)


@admin.register(WordProgress)
class WordProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'vocabulary', 'is_known', 'level', 'interval', 'next_review_date', 'last_reviewed')
    list_filter = ('is_known',)


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'total_reviews', 'last_review_date')


admin.site.register(JoinedList)
