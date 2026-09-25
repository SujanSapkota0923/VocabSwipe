"""Filling in missing meanings from the dictionary API.

A list uploaded as bare words is playable straight away; the meanings arrive
afterwards. The work runs in a daemon thread so the upload request returns at
once, and every step is written back to the database, so a restart mid-run
leaves a list that can be picked up again rather than one stuck at
"processing".
"""

import logging
import threading
import time

from django.db import close_old_connections

from .models import Vocabulary, WordList
from .utils.dictionary_api import DictionaryAPI

logger = logging.getLogger(__name__)

PAUSE_BETWEEN_WORDS = 0.5


def pending_words(word_list_id):
    return list(
        Vocabulary.objects
        .filter(word_list_id=word_list_id, meaning_1='')
        .order_by('id')
    )


def fetch_meanings_for_list(word_list_id, pause=PAUSE_BETWEEN_WORDS, progress=None):
    """Fill in every empty meaning in one list. Returns the number of words done.

    Safe to call again: it only looks at words that still have no meaning, so a
    run that was interrupted simply continues where it stopped.
    """
    try:
        word_list = WordList.objects.get(id=word_list_id)
    except WordList.DoesNotExist:
        logger.warning('Meaning lookup skipped, list %s is gone', word_list_id)
        return 0

    words = pending_words(word_list_id)
    if not words:
        word_list.processing_status = 'completed'
        word_list.words_processed = word_list.total_words
        word_list.save(update_fields=['processing_status', 'words_processed'])
        return 0

    WordList.objects.filter(id=word_list_id).update(processing_status='processing')
    logger.info('Meaning lookup started for list %s (%s words)', word_list_id, len(words))

    already_done = max((word_list.total_words or 0) - len(words), 0)
    done = 0
    for index, vocabulary in enumerate(words, 1):
        try:
            details = DictionaryAPI.fetch_word_details(vocabulary.word)
        except Exception:
            logger.exception('Dictionary lookup failed for %r', vocabulary.word)
            details = {}

        meanings = details.get('meanings') or []
        if meanings:
            vocabulary.meaning_1 = meanings[0]
            vocabulary.meaning_2 = meanings[1] if len(meanings) > 1 else None
            vocabulary.meaning_3 = meanings[2] if len(meanings) > 2 else None
            vocabulary.example_sentence = details.get('example')
            vocabulary.audio_url = details.get('audio_url')
        else:
            # The card stays playable; it just shows no definition.
            vocabulary.meaning_1 = f'No definition found for "{vocabulary.word}".'

        vocabulary.save(update_fields=[
            'meaning_1', 'meaning_2', 'meaning_3', 'example_sentence', 'audio_url',
        ])
        done += 1

        # Words already filled in by an earlier run still count towards progress.
        WordList.objects.filter(id=word_list_id).update(words_processed=already_done + index)

        if progress:
            progress(index, len(words))

        if pause and index < len(words):
            time.sleep(pause)

    WordList.objects.filter(id=word_list_id).update(
        processing_status='completed',
        words_processed=word_list.total_words or done,
    )
    logger.info('Meaning lookup finished for list %s', word_list_id)
    return done


_running = set()
_running_lock = threading.Lock()


def _run_in_thread(word_list_id):
    try:
        fetch_meanings_for_list(word_list_id)
    except Exception as exc:
        logger.exception('Meaning lookup crashed for list %s', word_list_id)
        WordList.objects.filter(id=word_list_id).update(
            processing_status='failed', error_message=str(exc)[:500]
        )
    finally:
        with _running_lock:
            _running.discard(word_list_id)
        close_old_connections()


def start_background_processing(word_list_id):
    """Kick off the lookup without blocking the request.

    Does nothing if this process is already working on the same list, so
    reloading the dashboard cannot pile up duplicate threads.
    """
    with _running_lock:
        if word_list_id in _running:
            return None
        _running.add(word_list_id)

    thread = threading.Thread(target=_run_in_thread, args=(word_list_id,), daemon=True)
    thread.start()
    logger.info('Background meaning lookup queued for list %s', word_list_id)
    return thread


def reset_interrupted_lists():
    """Move lists left mid-run by a restart back to 'pending'.

    Called once at startup. Without it a list whose worker was killed shows a
    progress bar that never moves.
    """
    stuck = WordList.objects.filter(processing_status='processing')
    count = stuck.update(processing_status='pending')
    if count:
        logger.info('Reset %s interrupted meaning lookup(s) to pending', count)
    return count


def resume_pending_lookups(word_lists):
    """Restart the lookup for any of these lists that is still waiting.

    The dashboard calls this, so a list left behind by a restart picks itself
    up the next time its owner looks at it.
    """
    started = 0
    for word_list in word_lists:
        if word_list.processing_status in ('pending', 'processing'):
            if start_background_processing(word_list.id) is not None:
                started += 1
    return started
