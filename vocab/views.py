from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import UploadFileForm
from .models import Vocabulary, WordList
from .utils.parsing import parse_vocabulary_file

def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                parsed_data = parse_vocabulary_file(file)
                
                if parsed_data:
                    # Create a new WordList entry
                    word_list = WordList.objects.create(
                        name=file.name,
                        file_name=file.name
                    )
                    
                    vocab_objects = []
                    for item in parsed_data:
                        meanings = item['meanings']
                        vocab_objects.append(Vocabulary(
                            word_list=word_list,
                            word=item['word'],
                            meaning_1=meanings[0] if len(meanings) > 0 else "",
                            meaning_2=meanings[1] if len(meanings) > 1 else None,
                            meaning_3=meanings[2] if len(meanings) > 2 else None,
                        ))
                    Vocabulary.objects.bulk_create(vocab_objects)
                    return redirect('game')
                else:
                    form.add_error('file', 'No valid data found in file.')
            except Exception as e:
                form.add_error('file', f'Error parsing file: {str(e)}')
    else:
        form = UploadFileForm()
    
    from django.db.models import Count, Q
    
    word_lists = WordList.objects.annotate(
        unknown_count=Count('words', filter=Q(words__is_known=False))
    ).order_by('-id')
    
    context = {
        'form': form,
        'word_lists': word_lists,
    }
    return render(request, 'upload.html', context)

def delete_list_view(request, list_id):
    if request.method == 'POST':
        password = request.POST.get('password')
        if password != 'sujandaijindabaad':
            # You might want to handle this better, e.g. with a message
            return redirect('upload')
            
        try:
            word_list = WordList.objects.get(id=list_id)
            word_list.delete()
        except WordList.DoesNotExist:
            pass
    return redirect('upload')

def game_view(request):
    return render(request, 'game.html')

def list_word_lists_api(request):
    lists = WordList.objects.all()
    data = []
    for l in lists:
        data.append({
            'id': l.id,
            'name': l.name,
            'count': l.words.count()
        })
    return JsonResponse(data, safe=False)

def card_list_api(request):
    list_id = request.GET.get('list_id')
    review_mode = request.GET.get('review_mode') == 'true'
    
    cards = Vocabulary.objects.all()

    if list_id:
        cards = cards.filter(word_list_id=list_id)
    
    if review_mode:
        cards = cards.filter(is_known=False)
        
    cards = cards.order_by('?')

    data = []
    for card in cards:
        meanings = [card.meaning_1]
        if card.meaning_2: meanings.append(card.meaning_2)
        if card.meaning_3: meanings.append(card.meaning_3)
        data.append({
            'id': card.id,
            'word': card.word,
            'meanings': meanings,
            'is_known': card.is_known
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def update_card_status_api(request, card_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_known = data.get('is_known', False)
            card = Vocabulary.objects.get(id=card_id)
            card.is_known = is_known
            card.save()
            return JsonResponse({'status': 'success'})
        except Vocabulary.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Card not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
