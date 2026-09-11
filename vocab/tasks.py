"""
Background task processing for vocabulary meaning fetching
"""

import threading
import time
from django.db import transaction
from .models import Vocabulary, WordList
from .utils.dictionary_api import DictionaryAPI


def process_word_chunk(word_list_id, chunk_words, chunk_number, total_chunks):
    """
    Process a chunk of words - fetch meanings and update database

    Args:
        word_list_id: ID of the WordList being processed
        chunk_words: List of Vocabulary objects to process
        chunk_number: Current chunk number (for logging)
        total_chunks: Total number of chunks
    """
    try:
        print(
            f"\n[Chunk {chunk_number}/{total_chunks}] Processing {len(chunk_words)} words..."
        )

        for idx, vocab_obj in enumerate(chunk_words, 1):
            # Skip if already has meaning
            if vocab_obj.meaning_1:
                continue

            # Fetch full details from API
            details = DictionaryAPI.fetch_word_details(vocab_obj.word)

            if details:
                meanings = details.get("meanings", [])
                vocab_obj.meaning_1 = meanings[0] if len(meanings) > 0 else ""
                vocab_obj.meaning_2 = meanings[1] if len(meanings) > 1 else None
                vocab_obj.meaning_3 = meanings[2] if len(meanings) > 2 else None

                # New fields
                vocab_obj.example_sentence = details.get("example")
                vocab_obj.audio_url = details.get("audio_url")
            else:
                # Placeholder if API fails
                vocab_obj.meaning_1 = f"Definition not found for '{vocab_obj.word}'"

            vocab_obj.save()

            # Update progress after EACH word (not just at the end of chunk)
            with transaction.atomic():
                word_list = WordList.objects.select_for_update().get(id=word_list_id)
                word_list.words_processed += 1
                word_list.save()

            # Add delay to avoid rate limiting
            if idx < len(chunk_words):
                time.sleep(0.5)

        print(f"[Chunk {chunk_number}/{total_chunks}] ✅ Completed!")

    except Exception as e:
        print(f"[Chunk {chunk_number}/{total_chunks}] ❌ Error: {e}")
        # Don't fail the entire process for one chunk error
        with transaction.atomic():
            word_list = WordList.objects.select_for_update().get(id=word_list_id)
            word_list.error_message = f"Error in chunk {chunk_number}: {str(e)}"
            word_list.save()


def process_word_list_background(word_list_id, chunk_size=50):
    """
    Background task to process all words in a WordList
    Divides words into chunks and processes them sequentially

    Args:
        word_list_id: ID of the WordList to process
        chunk_size: Number of words per chunk (default: 50)
    """
    try:
        print(f"\n{'='*60}")
        print(f"Background Processing Started")
        print(f"WordList ID: {word_list_id}")
        print(f"Chunk Size: {chunk_size}")
        print(f"{'='*60}\n")

        # Get the word list and update status
        word_list = WordList.objects.get(id=word_list_id)
        word_list.processing_status = "processing"
        word_list.save()

        # Get all words that need processing (empty meaning_1)
        words_to_process = list(
            Vocabulary.objects.filter(word_list_id=word_list_id, meaning_1="").order_by(
                "id"
            )
        )

        if not words_to_process:
            print("No words to process - all have meanings already")
            word_list.processing_status = "completed"
            word_list.save()
            return

        # Divide into chunks
        chunks = [
            words_to_process[i : i + chunk_size]
            for i in range(0, len(words_to_process), chunk_size)
        ]

        total_chunks = len(chunks)
        print(f"Total words to process: {len(words_to_process)}")
        print(f"Number of chunks: {total_chunks}")
        print(f"Words per chunk: {chunk_size}\n")

        # Process each chunk sequentially
        for chunk_num, chunk in enumerate(chunks, 1):
            process_word_chunk(word_list_id, chunk, chunk_num, total_chunks)

        # Mark as completed
        word_list.refresh_from_db()
        word_list.processing_status = "completed"
        word_list.save()

        print(f"\n{'='*60}")
        print(f"✅ Background Processing Completed!")
        print(
            f"Total words processed: {word_list.words_processed}/{word_list.total_words}"
        )
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Background Processing Failed: {e}\n")
        try:
            word_list = WordList.objects.get(id=word_list_id)
            word_list.processing_status = "failed"
            word_list.error_message = str(e)
            word_list.save()
        except:
            pass


def start_background_processing(word_list_id, chunk_size=50):
    """
    Start background processing in a separate thread

    Args:
        word_list_id: ID of the WordList to process
        chunk_size: Number of words per chunk (default: 50)
    """
    thread = threading.Thread(
        target=process_word_list_background,
        args=(word_list_id, chunk_size),
        daemon=True,
    )
    thread.start()
    print(f"🚀 Started background processing for WordList {word_list_id}")


def process_multiple_word_lists_sequential(word_list_ids):
    """
    Process multiple word lists sequentially in a single background thread
    This prevents overwhelming the API with concurrent requests

    Args:
        word_list_ids: List of WordList IDs to process sequentially
    """

    def process_all():
        print(f"\n{'='*60}")
        print(f"Sequential Processing Started")
        print(f"Total Parts: {len(word_list_ids)}")
        print(f"{'='*60}\n")

        for idx, word_list_id in enumerate(word_list_ids, 1):
            try:
                word_list = WordList.objects.get(id=word_list_id)
                print(
                    f"\n[Part {idx}/{len(word_list_ids)}] Processing: {word_list.name}"
                )
                process_word_list_background(word_list_id, chunk_size=50)
                print(
                    f"[Part {idx}/{len(word_list_ids)}] ✅ Completed: {word_list.name}"
                )
            except Exception as e:
                print(f"[Part {idx}/{len(word_list_ids)}] ❌ Error: {e}")

        print(f"\n{'='*60}")
        print(f"✅ All {len(word_list_ids)} parts processed!")
        print(f"{'='*60}\n")

    thread = threading.Thread(target=process_all, daemon=True)
    thread.start()
    print(f"🚀 Started sequential background processing for {len(word_list_ids)} parts")
