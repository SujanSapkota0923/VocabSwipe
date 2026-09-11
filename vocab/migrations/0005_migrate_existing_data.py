"""Give pre-auth lists an owner + share code, and move is_known into per-user progress."""
import secrets

from django.db import migrations

ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def forwards(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    WordList = apps.get_model('vocab', 'WordList')
    WordProgress = apps.get_model('vocab', 'WordProgress')

    owner = User.objects.filter(is_superuser=True).order_by('id').first() or User.objects.order_by('id').first()

    used = set(WordList.objects.exclude(share_code=None).values_list('share_code', flat=True))
    for word_list in WordList.objects.all():
        changed = False
        if owner and word_list.owner_id is None:
            word_list.owner_id = owner.id
            changed = True
        if not word_list.share_code:
            while True:
                code = ''.join(secrets.choice(ALPHABET) for _ in range(6))
                if code not in used:
                    break
            used.add(code)
            word_list.share_code = code
            changed = True
        if changed:
            word_list.save(update_fields=['owner', 'share_code'])

    if owner:
        Vocabulary = apps.get_model('vocab', 'Vocabulary')
        WordProgress.objects.bulk_create([
            WordProgress(
                user_id=owner.id,
                vocabulary_id=card.id,
                is_known=card.is_known,
                level=card.level,
                last_reviewed=card.last_reviewed,
                correct_count=1 if card.is_known else 0,
            )
            for card in Vocabulary.objects.filter(is_known=True)
        ], ignore_conflicts=True)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0004_auth_and_sharing'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
