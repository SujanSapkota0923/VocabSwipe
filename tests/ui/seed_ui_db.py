"""Demo data for tests/ui/viewport_check.js.

Run against a throwaway database, never the real one:

    DJANGO_DEBUG=1 DJANGO_DB_PATH=/tmp/vocabswipe-ui.sqlite3 python manage.py migrate
    DJANGO_DEBUG=1 DJANGO_DB_PATH=/tmp/vocabswipe-ui.sqlite3 python manage.py shell < tests/ui/seed_ui_db.py

Creates user `demo` / `demo-pass-123`, a 60-word private list with long
meanings (to exercise wrapping and the scrolling card back), and a 10-word
public list. On a fresh database the starter deck is list 1, so these are
lists 2 and 3, which is what the check expects by default.
"""

from django.contrib.auth.models import User

from vocab.models import UserStats, Vocabulary, WordList, WordProgress

LONG = ('Third meaning that is also quite long and should make the back of the card '
        'scroll when combined with an example sentence. ') * 3

user = User.objects.create_user('demo', password='demo-pass-123')

big = WordList.objects.create(
    owner=user, name='PTE Academic core vocabulary — part 1', description='High-frequency words',
    file_name='big.csv', total_words=60, words_processed=60,
)
Vocabulary.objects.bulk_create([
    Vocabulary(
        word_list=big,
        word='incomprehensibility' if i % 7 == 0 else f'word{i}',
        meaning_1='A fairly long first definition that wraps over a couple of lines on a phone screen.',
        meaning_2='Second meaning.' if i % 2 else None,
        meaning_3=LONG if i % 5 == 0 else None,
        example_sentence='The results were abundant and surprising.',
    )
    for i in range(60)
])

small = WordList.objects.create(
    owner=user, name='Short', file_name='small.csv', is_public=True, total_words=10, words_processed=10,
)
Vocabulary.objects.bulk_create([
    Vocabulary(word_list=small, word=f'w{i}', meaning_1='m') for i in range(10)
])

for vocabulary in big.words.all()[:20]:
    progress = WordProgress(user=user, vocabulary=vocabulary)
    progress.apply_review(True)
    progress.save()

stats = UserStats.get_stats(user)
stats.current_streak = 4
stats.save()

print(f'Seeded: big list {big.id}, small list {small.id}')
