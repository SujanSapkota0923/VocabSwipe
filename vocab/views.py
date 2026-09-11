from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json
from .forms import UploadFileForm
from .models import Vocabulary, WordList, UserStats
from .utils.parsing import parse_vocabulary_file
from .tasks import start_background_processing


def upload_view(request):
    # ... existing code ...
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            try:
                parsed_result = parse_vocabulary_file(file)

                if parsed_result and parsed_result.get("data"):
                    parsed_data = parsed_result["data"]
                    needs_api_fetch = parsed_result.get("needs_api_fetch", False)

                    # Split into chunks of 50 words
                    CHUNK_SIZE = 50
                    total_words = len(parsed_data)

                    # Calculate number of parts
                    num_parts = (total_words + CHUNK_SIZE - 1) // CHUNK_SIZE

                    # Base name for the word lists
                    base_name = file.name.rsplit(".", 1)[0]  # Remove extension

                    # Collect word list IDs that need processing
                    word_lists_to_process = []

                    # Create a WordList for each chunk
                    for part_num in range(num_parts):
                        start_idx = part_num * CHUNK_SIZE
                        end_idx = min((part_num + 1) * CHUNK_SIZE, total_words)
                        chunk_data = parsed_data[start_idx:end_idx]

                        # Create WordList with part number
                        if num_parts > 1:
                            list_name = (
                                f"{base_name} - Part {part_num + 1} of {num_parts}"
                            )
                        else:
                            list_name = base_name

                        word_list = WordList.objects.create(
                            name=list_name,
                            file_name=file.name,
                            total_words=len(chunk_data),
                            words_processed=0,
                            processing_status="pending",
                        )

                        # Create Vocabulary entries for this chunk
                        vocab_objects = []
                        for item in chunk_data:
                            meanings = item["meanings"]
                            vocab_objects.append(
                                Vocabulary(
                                    word_list=word_list,
                                    word=item["word"],
                                    meaning_1=meanings[0] if len(meanings) > 0 else "",
                                    meaning_2=(
                                        meanings[1] if len(meanings) > 1 else None
                                    ),
                                    meaning_3=(
                                        meanings[2] if len(meanings) > 2 else None
                                    ),
                                )
                            )

                        Vocabulary.objects.bulk_create(vocab_objects)

                        # Check if this chunk needs API processing
                        if needs_api_fetch:
                            words_to_fetch = sum(
                                1
                                for item in chunk_data
                                if item.get("needs_fetch", False)
                            )
                            if words_to_fetch > 0:
                                word_lists_to_process.append(word_list.id)
                        else:
                            # All meanings provided - mark as completed immediately
                            word_list.processing_status = "completed"
                            word_list.words_processed = len(chunk_data)
                            word_list.save()

                    # Start sequential background processing for all parts that need it
                    if word_lists_to_process:
                        print(
                            f"\n🚀 Starting sequential background processing for {len(word_lists_to_process)} parts..."
                        )
                        from .tasks import process_multiple_word_lists_sequential

                        process_multiple_word_lists_sequential(word_lists_to_process)

                    return redirect(
                        "upload"
                    )  # Redirect to upload page to show all parts
                else:
                    form.add_error("file", "No valid data found in file.")
            except Exception as e:
                form.add_error("file", f"Error parsing file: {str(e)}")
    else:
        form = UploadFileForm()

    # Word of the Day - 10 random words that change daily
    from datetime import date
    import random

    # Use today's date as seed for consistent daily selection
    today = date.today()
    seed = int(today.strftime("%Y%m%d"))  # e.g., 20260125

    # Get all completed vocabulary words
    all_words = Vocabulary.objects.filter(
        word_list__processing_status="completed"
    ).exclude(meaning_1="")

    word_of_day = []
    if all_words.exists():
        # Set seed for reproducible random selection
        random.seed(seed)
        # Get 10 random words
        word_count = min(10, all_words.count())
        word_of_day = random.sample(list(all_words), word_count)

    from django.db.models import Count, Q

    word_lists = WordList.objects.annotate(
        unknown_count=Count("words", filter=Q(words__is_known=False))
    ).order_by("-id")

    context = {
        "form": form,
        "word_lists": word_lists,
        "word_of_day": word_of_day,
    }
    return render(request, "upload.html", context)


def delete_list_view(request, list_id):
    if request.method == "POST":
        password = request.POST.get("password")
        if password != settings.API_PASSWORD:
            # You might want to handle this better, e.g. with a message
            return redirect("upload")

        try:
            word_list = WordList.objects.get(id=list_id)
            word_list.delete()
        except WordList.DoesNotExist:
            pass
    return redirect("upload")


def game_view(request):
    return render(request, "game.html")


def list_word_lists_api(request):
    lists = WordList.objects.all()
    data = []
    for l in lists:
        data.append({"id": l.id, "name": l.name, "count": l.words.count()})
    return JsonResponse(data, safe=False)


def card_list_api(request):
    list_id = request.GET.get("list_id")
    review_mode = request.GET.get("review_mode") == "true"

    cards = Vocabulary.objects.all()

    if list_id:
        cards = cards.filter(word_list_id=list_id)

    if review_mode:
        # Show cards due for review OR cards never reviewed
        now = timezone.now()
        cards = cards.filter(
            models.Q(next_review_date__lte=now)
            | models.Q(next_review_date__isnull=True)
        ).filter(is_known=False)

    cards = cards.order_by("?")

    data = []
    for card in cards:
        meanings = [card.meaning_1]
        if card.meaning_2:
            meanings.append(card.meaning_2)
        if card.meaning_3:
            meanings.append(card.meaning_3)
        data.append(
            {
                "id": card.id,
                "word": card.word,
                "meanings": meanings,
                "is_known": card.is_known,
                "example": card.example_sentence,
                "audio_url": card.audio_url,
            }
        )
    return JsonResponse(data, safe=False)


@csrf_exempt
def update_card_status_api(request, card_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            is_known = data.get("is_known", False)
            card = Vocabulary.objects.get(id=card_id)

            # SM-2 Algorithm Implementation
            # q: quality of response (0-5).
            # Swipe Right (Known) -> q=4 (good response)
            # Swipe Left (Unknown) -> q=0 (blackout)
            q = 4 if is_known else 0

            if q >= 3:  # Correct response
                if card.repetition_count == 0:
                    card.interval = 1
                elif card.repetition_count == 1:
                    card.interval = 6
                else:
                    card.interval = round(card.interval * card.easiness_factor)

                card.repetition_count += 1
            else:  # Incorrect response
                card.repetition_count = 0
                card.interval = 1

            # Update Easiness Factor (EF)
            # EF := EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            card.easiness_factor = card.easiness_factor + (
                0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
            )
            if card.easiness_factor < 1.3:
                card.easiness_factor = 1.3

            card.is_known = is_known
            card.last_reviewed = timezone.now()
            card.next_review_date = timezone.now() + timedelta(days=card.interval)

            card.save()

            # Update user streak
            stats = UserStats.get_stats()
            stats.update_streak()

            return JsonResponse(
                {
                    "status": "success",
                    "next_review": card.next_review_date.isoformat(),
                    "interval": card.interval,
                    "streak": stats.current_streak,
                }
            )
        except Vocabulary.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Card not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)


@csrf_exempt
def word_list_progress_api(request, list_id):
    """
    API endpoint to check processing progress of a word list
    """
    try:
        word_list = WordList.objects.get(id=list_id)
        return JsonResponse(
            {
                "id": word_list.id,
                "name": word_list.name,
                "status": word_list.processing_status,
                "total_words": word_list.total_words,
                "words_processed": word_list.words_processed,
                "progress_percentage": word_list.progress_percentage,
                "error_message": word_list.error_message,
            }
        )
    except WordList.DoesNotExist:
        return JsonResponse({"error": "Word list not found"}, status=404)


def user_stats_api(request):
    """
    API endpoint to get user learning stats
    """
    stats = UserStats.get_stats()
    return JsonResponse(
        {
            "current_streak": stats.current_streak,
            "total_reviews": stats.total_reviews,
            "last_review_date": (
                stats.last_review_date.isoformat() if stats.last_review_date else None
            ),
        }
    )
