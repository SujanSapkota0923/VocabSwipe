import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import JoinCodeForm, ListSettingsForm, SignupForm, UploadFileForm
from .models import JoinedList, UserStats, Vocabulary, WordList, WordProgress
from .tasks import start_background_processing
from .utils.parsing import parse_vocabulary_file

GAME_MODES = ('classic', 'timer')
SESSION_UNLOCKED = 'unlocked_codes'


# ---------------------------------------------------------------- access


def accessible_lists(user):
    """Lists a signed-in user owns plus lists they joined with a code."""
    return WordList.objects.filter(
        Q(owner=user) | Q(joined_by__user=user)
    ).distinct()


def unlocked_codes(request):
    return request.session.get(SESSION_UNLOCKED, [])


def unlock_code(request, code):
    codes = unlocked_codes(request)
    if code not in codes:
        request.session[SESSION_UNLOCKED] = codes + [code]


def can_play(request, word_list):
    """Public lists are open to everyone. Private ones need ownership,
    a join, or the share code entered in this browser session."""
    if word_list is None:
        return False
    if word_list.is_public:
        return True
    if word_list.share_code in unlocked_codes(request):
        return True
    user = request.user
    if user.is_authenticated:
        if word_list.owner_id == user.id:
            return True
        if JoinedList.objects.filter(user=user, word_list=word_list).exists():
            return True
    return False


def playable_lists(request, list_id=None):
    """Queryset of Vocabulary sources for the current request."""
    if list_id:
        word_list = WordList.objects.filter(id=list_id).first()
        if not can_play(request, word_list):
            return WordList.objects.none()
        return WordList.objects.filter(id=word_list.id)
    if request.user.is_authenticated:
        return accessible_lists(request.user)
    codes = unlocked_codes(request)
    return WordList.objects.filter(share_code__in=codes)


def find_by_code(code):
    return WordList.objects.filter(share_code=(code or '').strip().upper()).first()


# ---------------------------------------------------------------- pages


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    join_form = JoinCodeForm()
    if request.method == 'POST':
        join_form = JoinCodeForm(request.POST)
        if join_form.is_valid():
            code = join_form.cleaned_data['code']
            word_list = find_by_code(code)
            if not word_list:
                join_form.add_error('code', 'No list found with that code.')
            else:
                unlock_code(request, word_list.share_code)
                return redirect(f"/game/?list_id={word_list.id}")

    public_lists = (
        WordList.objects.filter(is_public=True)
        .annotate(total=Count('words'))
        .select_related('owner')[:6]
    )
    return render(request, 'home.html', {
        'join_form': join_form,
        'public_lists': public_lists,
        'public_count': WordList.objects.filter(is_public=True).count(),
    })


def explore_view(request):
    query = request.GET.get('q', '').strip()
    lists = WordList.objects.filter(is_public=True).annotate(total=Count('words')).select_related('owner')
    if query:
        lists = lists.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'explore.html', {'lists': lists, 'query': query})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Carry any decks unlocked while signed out into the account.
            for code in unlocked_codes(request):
                word_list = find_by_code(code)
                if word_list and word_list.owner_id != user.id:
                    JoinedList.objects.get_or_create(user=user, word_list=word_list)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard_view(request):
    upload_form = UploadFileForm()
    join_form = JoinCodeForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'upload')

        if action == 'join':
            join_form = JoinCodeForm(request.POST)
            if join_form.is_valid():
                code = join_form.cleaned_data['code']
                word_list = find_by_code(code)
                if not word_list:
                    join_form.add_error('code', 'No list found with that code.')
                elif word_list.owner_id == request.user.id:
                    join_form.add_error('code', 'That is your own list.')
                else:
                    JoinedList.objects.get_or_create(user=request.user, word_list=word_list)
                    messages.success(request, f'Joined "{word_list.name}".')
                    return redirect('dashboard')
        else:
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                uploaded = request.FILES['file']
                try:
                    parsed_result = parse_vocabulary_file(uploaded)
                except Exception as exc:
                    parsed_result = None
                    upload_form.add_error('file', f'Error parsing file: {exc}')

                parsed_data = (parsed_result or {}).get('data')
                needs_api_fetch = (parsed_result or {}).get('needs_api_fetch', False)

                if parsed_data:
                    word_list = WordList.objects.create(
                        owner=request.user,
                        name=upload_form.cleaned_data.get('name') or uploaded.name,
                        description=upload_form.cleaned_data.get('description', ''),
                        file_name=uploaded.name,
                        is_public=upload_form.cleaned_data.get('is_public', False),
                        total_words=len(parsed_data),
                        words_processed=0 if needs_api_fetch else len(parsed_data),
                        processing_status='pending' if needs_api_fetch else 'completed',
                    )
                    Vocabulary.objects.bulk_create([
                        Vocabulary(
                            word_list=word_list,
                            word=item['word'],
                            meaning_1=item['meanings'][0] if item['meanings'] else '',
                            meaning_2=item['meanings'][1] if len(item['meanings']) > 1 else None,
                            meaning_3=item['meanings'][2] if len(item['meanings']) > 2 else None,
                        )
                        for item in parsed_data
                    ])

                    if needs_api_fetch:
                        # Words uploaded without a meaning get one from the dictionary API.
                        start_background_processing(word_list.id)
                        messages.success(
                            request,
                            f'Added {len(parsed_data)} words. Looking up the missing meanings now.',
                        )
                    else:
                        messages.success(request, f'Added {len(parsed_data)} words.')
                    return redirect('dashboard')
                elif parsed_result is not None:
                    upload_form.add_error('file', 'No valid data found in file.')

    known_ids = set(
        WordProgress.objects.filter(user=request.user, is_known=True)
        .values_list('vocabulary_id', flat=True)
    )

    def decorate(lists):
        out = []
        for word_list in lists:
            word_ids = set(word_list.words.values_list('id', flat=True))
            out.append({
                'obj': word_list,
                'total': len(word_ids),
                'known': len(word_ids & known_ids),
                'unknown': len(word_ids - known_ids),
            })
        return out

    my_lists = decorate(WordList.objects.filter(owner=request.user))
    joined = decorate(WordList.objects.filter(joined_by__user=request.user).select_related('owner'))

    total_words = Vocabulary.objects.filter(word_list__in=accessible_lists(request.user)).count()
    stats = UserStats.get_stats(request.user)

    return render(request, 'dashboard.html', {
        'form': upload_form,
        'join_form': join_form,
        'my_lists': my_lists,
        'joined_lists': joined,
        'total_words': total_words,
        'known_total': len(known_ids),
        'stats': stats,
    })


@login_required
def list_settings_view(request, list_id):
    word_list = get_object_or_404(WordList, id=list_id, owner=request.user)
    if request.method == 'POST':
        form = ListSettingsForm(request.POST, instance=word_list)
        if form.is_valid():
            form.save()
            messages.success(request, 'List updated.')
            return redirect('dashboard')
    else:
        form = ListSettingsForm(instance=word_list)
    return render(request, 'list_settings.html', {'form': form, 'word_list': word_list})


@login_required
def toggle_public_view(request, list_id):
    if request.method == 'POST':
        word_list = WordList.objects.filter(id=list_id, owner=request.user).first()
        if word_list:
            word_list.is_public = not word_list.is_public
            word_list.save(update_fields=['is_public'])
            messages.success(
                request,
                f'"{word_list.name}" is now {"public" if word_list.is_public else "private"}.',
            )
    return redirect('dashboard')


@login_required
def delete_list_view(request, list_id):
    if request.method == 'POST':
        word_list = WordList.objects.filter(id=list_id, owner=request.user).first()
        if word_list:
            word_list.delete()
            messages.success(request, 'List deleted.')
        else:
            messages.error(request, 'You can only delete your own lists.')
    return redirect('dashboard')


@login_required
def leave_list_view(request, list_id):
    if request.method == 'POST':
        JoinedList.objects.filter(user=request.user, word_list_id=list_id).delete()
        messages.success(request, 'Removed from your lists.')
    return redirect('dashboard')


def game_view(request):
    mode = request.GET.get('mode', 'classic')
    if mode not in GAME_MODES:
        mode = 'classic'

    code = request.GET.get('code')
    if code:
        word_list = find_by_code(code)
        if word_list:
            unlock_code(request, word_list.share_code)
            return redirect(f'/game/?list_id={word_list.id}&mode={mode}')
        messages.error(request, 'No list found with that code.')
        return redirect('home')

    list_id = request.GET.get('list_id')
    word_list = None
    if list_id:
        word_list = WordList.objects.filter(id=list_id).select_related('owner').first()
        if not can_play(request, word_list):
            messages.error(request, 'That list is private. Ask its owner for the share code.')
            return redirect('home')
    elif not request.user.is_authenticated:
        return redirect('home')

    try:
        seconds = int(request.GET.get('seconds', 10))
    except ValueError:
        seconds = 10
    seconds = max(3, min(seconds, 120))

    return render(request, 'game.html', {
        'mode': mode,
        'seconds': seconds,
        'word_list': word_list,
        'review_mode': request.GET.get('review_mode') == 'true',
    })


# ---------------------------------------------------------------- api


@login_required
def list_word_lists_api(request):
    data = [
        {
            'id': word_list.id,
            'name': word_list.name,
            'share_code': word_list.share_code,
            'count': word_list.words.count(),
            'owned': word_list.owner_id == request.user.id,
            'is_public': word_list.is_public,
            'processing_status': word_list.processing_status,
        }
        for word_list in accessible_lists(request.user)
    ]
    return JsonResponse(data, safe=False)


def card_list_api(request):
    list_id = request.GET.get('list_id')
    review_mode = request.GET.get('review_mode') == 'true'

    lists = playable_lists(request, list_id)
    cards = Vocabulary.objects.filter(word_list__in=lists)

    known_ids = set()
    if request.user.is_authenticated:
        progress = WordProgress.objects.filter(user=request.user, vocabulary__in=cards)
        known_ids = set(progress.filter(is_known=True).values_list('vocabulary_id', flat=True))

        if review_mode:
            # Drop known words whose next review date has not arrived yet.
            not_due = set(
                progress.filter(is_known=True, next_review_date__gt=timezone.now())
                .values_list('vocabulary_id', flat=True)
            )
            cards = cards.exclude(id__in=not_due)

    cards = cards.order_by('?')

    data = [
        {
            'id': card.id,
            'word': card.word,
            'meanings': card.meanings,
            'example': card.example_sentence,
            'audio_url': card.audio_url,
            'is_known': card.id in known_ids,
        }
        for card in cards
    ]
    return JsonResponse(data, safe=False)


def update_card_status_api(request, card_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

    if not request.user.is_authenticated:
        # Guests play without an account; progress stays in their browser.
        return JsonResponse({'status': 'guest'})

    card = Vocabulary.objects.filter(id=card_id).select_related('word_list').first()
    if not card or not can_play(request, card.word_list):
        return JsonResponse({'status': 'error', 'message': 'Card not found'}, status=404)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    is_known = bool(payload.get('is_known', False))

    progress, _ = WordProgress.objects.get_or_create(user=request.user, vocabulary=card)
    progress.apply_review(is_known)
    progress.save()

    stats = UserStats.get_stats(request.user)
    stats.update_streak()

    return JsonResponse({
        'status': 'success',
        'level': progress.level,
        'interval': progress.interval,
        'next_review': progress.next_review_date.isoformat(),
        'streak': stats.current_streak,
    })


def word_list_progress_api(request, list_id):
    """Meaning-lookup progress for one list, polled while it is still processing."""
    word_list = WordList.objects.filter(id=list_id).first()
    if not word_list or not can_play(request, word_list):
        return JsonResponse({'error': 'Word list not found'}, status=404)

    return JsonResponse({
        'id': word_list.id,
        'name': word_list.name,
        'status': word_list.processing_status,
        'total_words': word_list.total_words,
        'words_processed': word_list.words_processed,
        'progress_percentage': word_list.progress_percentage,
        'error_message': word_list.error_message,
    })


@login_required
def user_stats_api(request):
    stats = UserStats.get_stats(request.user)
    return JsonResponse({
        'current_streak': stats.current_streak,
        'longest_streak': stats.longest_streak,
        'total_reviews': stats.total_reviews,
        'last_review_date': stats.last_review_date.isoformat() if stats.last_review_date else None,
    })
