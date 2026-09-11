import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import JoinCodeForm, SignupForm, UploadFileForm
from .models import JoinedList, Vocabulary, WordList, WordProgress
from .utils.parsing import parse_vocabulary_file

GAME_MODES = ('classic', 'timer')


def accessible_lists(user):
    """Lists the user owns plus lists they joined with a code."""
    return WordList.objects.filter(
        Q(owner=user) | Q(joined_by__user=user)
    ).distinct()


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
                word_list = WordList.objects.filter(share_code=code).first()
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
                    parsed_data = parse_vocabulary_file(uploaded)
                except Exception as exc:
                    parsed_data = None
                    upload_form.add_error('file', f'Error parsing file: {exc}')

                if parsed_data:
                    word_list = WordList.objects.create(
                        owner=request.user,
                        name=upload_form.cleaned_data.get('name') or uploaded.name,
                        file_name=uploaded.name,
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
                    messages.success(request, f'Added {len(parsed_data)} words.')
                    return redirect('dashboard')
                elif parsed_data is not None:
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

    my_lists = decorate(
        WordList.objects.filter(owner=request.user).annotate(n=Count('words'))
    )
    joined = decorate(
        WordList.objects.filter(joined_by__user=request.user).select_related('owner')
    )

    total_words = Vocabulary.objects.filter(word_list__in=accessible_lists(request.user)).count()

    return render(request, 'dashboard.html', {
        'form': upload_form,
        'join_form': join_form,
        'my_lists': my_lists,
        'joined_lists': joined,
        'total_words': total_words,
        'known_total': len(known_ids),
    })


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


@login_required
def game_view(request):
    mode = request.GET.get('mode', 'classic')
    if mode not in GAME_MODES:
        mode = 'classic'

    list_id = request.GET.get('list_id')
    word_list = None
    if list_id:
        word_list = get_object_or_404(accessible_lists(request.user), id=list_id)

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


@login_required
def list_word_lists_api(request):
    data = [
        {
            'id': word_list.id,
            'name': word_list.name,
            'share_code': word_list.share_code,
            'count': word_list.words.count(),
            'owned': word_list.owner_id == request.user.id,
        }
        for word_list in accessible_lists(request.user)
    ]
    return JsonResponse(data, safe=False)


@login_required
def card_list_api(request):
    list_id = request.GET.get('list_id')
    review_mode = request.GET.get('review_mode') == 'true'

    lists = accessible_lists(request.user)
    if list_id:
        lists = lists.filter(id=list_id)

    cards = Vocabulary.objects.filter(word_list__in=lists)

    known_ids = set(
        WordProgress.objects.filter(user=request.user, is_known=True, vocabulary__in=cards)
        .values_list('vocabulary_id', flat=True)
    )
    if review_mode:
        cards = cards.exclude(id__in=known_ids)

    cards = cards.order_by('?')

    data = [
        {
            'id': card.id,
            'word': card.word,
            'meanings': card.meanings,
            'is_known': card.id in known_ids,
        }
        for card in cards
    ]
    return JsonResponse(data, safe=False)


@login_required
def update_card_status_api(request, card_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

    card = Vocabulary.objects.filter(
        id=card_id, word_list__in=accessible_lists(request.user)
    ).first()
    if not card:
        return JsonResponse({'status': 'error', 'message': 'Card not found'}, status=404)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    is_known = bool(payload.get('is_known', False))

    progress, _ = WordProgress.objects.get_or_create(user=request.user, vocabulary=card)
    progress.is_known = is_known
    progress.last_reviewed = timezone.now()
    if is_known:
        progress.correct_count += 1
        progress.level += 1
    else:
        progress.wrong_count += 1
        progress.level = 0
    progress.save()

    return JsonResponse({'status': 'success', 'level': progress.level})
