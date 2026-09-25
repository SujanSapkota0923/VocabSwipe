"""Tests for the parts that have to work on a fresh deploy: the pages render,
the card API returns cards, uploads parse, and progress is saved.
"""

import io
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import JoinedList, UserStats, Vocabulary, WordList, WordProgress
from .utils.parsing import ParseError, parse_vocabulary_file


def make_list(owner=None, name='Deck', public=True, words=('alpha', 'beta', 'gamma')):
    word_list = WordList.objects.create(
        owner=owner, name=name, file_name='f.csv', is_public=public, total_words=len(words)
    )
    Vocabulary.objects.bulk_create([
        Vocabulary(word_list=word_list, word=word, meaning_1=f'meaning of {word}')
        for word in words
    ])
    return word_list


def upload(name, content):
    return SimpleUploadedFile(name, content.encode('utf-8'), content_type='text/plain')


class StarterDeckTests(TestCase):
    """The migration ships a deck, so a new install is never empty."""

    def test_starter_deck_is_public_and_playable(self):
        deck = WordList.objects.filter(share_code='START1').first()
        self.assertIsNotNone(deck, 'starter deck missing — new installs would have nothing to play')
        self.assertTrue(deck.is_public)
        self.assertGreaterEqual(deck.words.count(), 50)
        self.assertFalse(deck.words.filter(meaning_1='').exists())

    def test_guest_can_play_starter_deck_from_a_fresh_database(self):
        deck = WordList.objects.get(share_code='START1')
        response = self.client.get(reverse('card_list_api'), {'list_id': deck.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), deck.words.count())


class PageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('player', password='swordfish-42')
        self.deck = make_list(owner=self.user, name='My deck')

    def test_public_pages_render_for_a_guest(self):
        for name in ('home', 'explore', 'login', 'signup'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_game_page_renders_for_a_public_list(self):
        response = self.client.get(reverse('game'), {'list_id': self.deck.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="card-stack"')
        self.assertContains(response, 'js/game.js')

    def test_pages_reference_the_local_stylesheet_not_a_cdn(self):
        body = self.client.get(reverse('home')).content.decode()
        self.assertIn('css/app.css', body)
        self.assertNotIn('cdn.tailwindcss.com', body)
        self.assertNotIn('fonts.googleapis.com', body)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_for_its_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My deck')

    def test_private_list_is_refused_without_the_code(self):
        private = make_list(owner=self.user, name='Private', public=False)
        response = self.client.get(reverse('game'), {'list_id': private.id})
        self.assertRedirects(response, reverse('home'))

    def test_share_code_unlocks_a_private_list_for_a_guest(self):
        private = make_list(owner=self.user, name='Private', public=False)
        response = self.client.get(reverse('game'), {'code': private.share_code})
        self.assertEqual(response.status_code, 302)
        cards = self.client.get(reverse('card_list_api'), {'list_id': private.id})
        self.assertEqual(len(cards.json()), 3)

    def test_signup_creates_an_account_and_signs_in(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newcomer',
            'password1': 'a-long-test-password-9',
            'password2': 'a-long-test-password-9',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='newcomer').exists())


class CardApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('player', password='swordfish-42')
        self.deck = make_list(owner=self.user)

    def test_cards_carry_everything_the_card_face_needs(self):
        response = self.client.get(reverse('card_list_api'), {'list_id': self.deck.id})
        card = response.json()[0]
        self.assertEqual(
            set(card), {'id', 'word', 'meanings', 'example', 'audio_url', 'is_known'}
        )
        self.assertTrue(card['word'])
        self.assertTrue(card['meanings'])

    def test_guest_without_a_list_gets_an_empty_deck_not_an_error(self):
        response = self.client.get(reverse('card_list_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_private_list_returns_nothing_to_a_stranger(self):
        private = make_list(owner=self.user, name='Private', public=False)
        stranger = User.objects.create_user('stranger', password='swordfish-42')
        self.client.force_login(stranger)
        response = self.client.get(reverse('card_list_api'), {'list_id': private.id})
        self.assertEqual(response.json(), [])

    def test_signed_in_player_gets_every_accessible_list(self):
        other = User.objects.create_user('friend', password='swordfish-42')
        joined = make_list(owner=other, name='Friend deck', public=False)
        JoinedList.objects.create(user=self.user, word_list=joined)

        self.client.force_login(self.user)
        response = self.client.get(reverse('card_list_api'))
        self.assertEqual(len(response.json()), 6)

    def test_answering_a_card_saves_progress_and_the_streak(self):
        self.client.force_login(self.user)
        card = self.deck.words.first()

        response = self.client.post(
            reverse('update_card_status_api', args=[card.id]),
            data=json.dumps({'is_known': True}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'success')
        self.assertEqual(payload['streak'], 1)

        progress = WordProgress.objects.get(user=self.user, vocabulary=card)
        self.assertTrue(progress.is_known)
        self.assertEqual(progress.interval, 1)
        self.assertIsNotNone(progress.next_review_date)

    def test_guest_answer_is_accepted_without_writing_progress(self):
        card = self.deck.words.first()
        response = self.client.post(
            reverse('update_card_status_api', args=[card.id]),
            data=json.dumps({'is_known': True}),
            content_type='application/json',
        )
        self.assertEqual(response.json()['status'], 'guest')
        self.assertEqual(WordProgress.objects.count(), 0)

    def test_review_mode_hides_words_that_are_not_due_yet(self):
        self.client.force_login(self.user)
        card = self.deck.words.first()
        progress = WordProgress.objects.create(user=self.user, vocabulary=card)
        progress.apply_review(True)
        progress.next_review_date = timezone.now() + timezone.timedelta(days=3)
        progress.save()

        response = self.client.get(
            reverse('card_list_api'), {'list_id': self.deck.id, 'review_mode': 'true'}
        )
        returned = {c['id'] for c in response.json()}
        self.assertNotIn(card.id, returned)
        self.assertEqual(len(returned), 2)

    def test_status_endpoint_rejects_get(self):
        card = self.deck.words.first()
        response = self.client.get(reverse('update_card_status_api', args=[card.id]))
        self.assertEqual(response.status_code, 405)


class UploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('uploader', password='swordfish-42')
        self.client.force_login(self.user)

    def post_file(self, uploaded, **extra):
        data = {'action': 'upload', 'file': uploaded, 'name': 'Uploaded'}
        data.update(extra)
        return self.client.post(reverse('dashboard'), data)

    def test_csv_with_meanings_is_playable_immediately(self):
        response = self.post_file(upload('words.csv', 'word,meaning\nglib,fluent but insincere\nwry,dryly humorous\n'))
        self.assertRedirects(response, reverse('dashboard'))

        word_list = WordList.objects.get(name='Uploaded')
        self.assertEqual(word_list.words.count(), 2)
        self.assertEqual(word_list.processing_status, 'completed')
        self.assertEqual(word_list.words.get(word='glib').meaning_1, 'fluent but insincere')

    def test_multiple_meanings_are_split_on_semicolons(self):
        self.post_file(upload('words.csv', 'bank, a place for money; the side of a river\n'))
        card = Vocabulary.objects.get(word='bank')
        self.assertEqual(card.meaning_1, 'a place for money')
        self.assertEqual(card.meaning_2, 'the side of a river')

    def test_quoted_commas_survive(self):
        self.post_file(upload('words.csv', 'tally,"a running count, kept by hand"\n'))
        self.assertEqual(Vocabulary.objects.get(word='tally').meaning_1, 'a running count, kept by hand')

    @patch('vocab.views.start_background_processing')
    def test_bare_word_list_queues_a_meaning_lookup(self, start_lookup):
        self.post_file(upload('words.txt', 'quixotic\nlaconic\n'))
        word_list = WordList.objects.get(name='Uploaded')
        self.assertEqual(word_list.processing_status, 'pending')
        self.assertEqual(word_list.words.count(), 2)
        start_lookup.assert_called_once_with(word_list.id)

    def test_duplicate_words_are_collapsed(self):
        self.post_file(upload('words.csv', 'same,one\nSAME,two\nother,three\n'))
        self.assertEqual(WordList.objects.get(name='Uploaded').words.count(), 2)

    def test_unsupported_file_type_is_rejected(self):
        response = self.post_file(upload('words.pdf', 'nope'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WordList.objects.filter(name='Uploaded').exists())
        self.assertContains(response, 'file types')

    def test_empty_file_reports_an_error_instead_of_making_a_dead_list(self):
        response = self.post_file(upload('words.csv', '\n\n'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WordList.objects.filter(name='Uploaded').exists())


class ParsingTests(TestCase):
    def parse(self, name, content):
        return parse_vocabulary_file(upload(name, content))

    def test_header_row_is_skipped(self):
        result = self.parse('w.csv', 'Word,Meaning\nzeal,great energy\n')
        self.assertEqual([e['word'] for e in result['data']], ['zeal'])

    def test_bare_words_are_flagged_for_lookup(self):
        result = self.parse('w.txt', 'zeal\nardour\n')
        self.assertTrue(result['needs_api_fetch'])
        self.assertTrue(all(e['needs_fetch'] for e in result['data']))

    def test_at_most_three_meanings_are_kept(self):
        result = self.parse('w.csv', 'set,a;b;c;d\n')
        self.assertEqual(result['data'][0]['meanings'], ['a', 'b', 'c'])

    def test_latin1_file_still_parses(self):
        raw = 'café,a coffee house\n'.encode('latin-1')
        result = parse_vocabulary_file(SimpleUploadedFile('w.csv', raw))
        self.assertEqual(result['data'][0]['word'], 'café')

    def test_xlsx_is_parsed_without_pandas(self):
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Word', 'Meaning'])
        sheet.append(['torpid', 'sluggish and inactive'])
        sheet.append(['vivid', 'bright; intense'])
        buffer = io.BytesIO()
        workbook.save(buffer)

        result = parse_vocabulary_file(SimpleUploadedFile('w.xlsx', buffer.getvalue()))
        self.assertEqual([e['word'] for e in result['data']], ['torpid', 'vivid'])
        self.assertEqual(result['data'][1]['meanings'], ['bright', 'intense'])

    def test_unreadable_type_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.parse('w.docx', 'anything')


class LookupRecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('owner', password='swordfish-42')

    def test_interrupted_lookup_is_reset_to_pending(self):
        from .tasks import reset_interrupted_lists

        word_list = make_list(owner=self.user)
        WordList.objects.filter(id=word_list.id).update(processing_status='processing')

        self.assertEqual(reset_interrupted_lists(), 1)
        word_list.refresh_from_db()
        self.assertEqual(word_list.processing_status, 'pending')

    @patch('vocab.tasks.DictionaryAPI.fetch_word_details')
    def test_lookup_fills_meanings_and_marks_the_list_complete(self, fetch):
        fetch.return_value = {
            'meanings': ['first sense', 'second sense'],
            'example': 'An example.',
            'audio_url': None,
        }
        from .tasks import fetch_meanings_for_list

        word_list = WordList.objects.create(
            owner=self.user, name='Bare', file_name='f.txt', total_words=2,
            processing_status='pending',
        )
        Vocabulary.objects.bulk_create([
            Vocabulary(word_list=word_list, word='alpha', meaning_1=''),
            Vocabulary(word_list=word_list, word='beta', meaning_1=''),
        ])

        self.assertEqual(fetch_meanings_for_list(word_list.id, pause=0), 2)
        word_list.refresh_from_db()
        self.assertEqual(word_list.processing_status, 'completed')
        self.assertEqual(word_list.words_processed, 2)
        self.assertEqual(word_list.words.get(word='alpha').meaning_1, 'first sense')
        self.assertEqual(word_list.words.get(word='alpha').meaning_2, 'second sense')

    @patch('vocab.tasks.DictionaryAPI.fetch_word_details', side_effect=OSError('network down'))
    def test_a_failing_dictionary_still_leaves_playable_cards(self, fetch):
        from .tasks import fetch_meanings_for_list

        word_list = WordList.objects.create(
            owner=self.user, name='Bare', file_name='f.txt', total_words=1,
            processing_status='pending',
        )
        Vocabulary.objects.create(word_list=word_list, word='alpha', meaning_1='')

        fetch_meanings_for_list(word_list.id, pause=0)
        word_list.refresh_from_db()
        self.assertEqual(word_list.processing_status, 'completed')
        self.assertIn('No definition found', word_list.words.get(word='alpha').meaning_1)


class SpacedRepetitionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('player', password='swordfish-42')
        self.card = make_list(owner=self.user).words.first()

    def test_intervals_grow_while_answers_stay_right(self):
        progress = WordProgress.objects.create(user=self.user, vocabulary=self.card)
        progress.apply_review(True)
        self.assertEqual(progress.interval, 1)
        progress.apply_review(True)
        self.assertEqual(progress.interval, 6)
        progress.apply_review(True)
        self.assertGreater(progress.interval, 6)

    def test_a_wrong_answer_sends_the_word_back_to_the_start(self):
        progress = WordProgress.objects.create(user=self.user, vocabulary=self.card)
        progress.apply_review(True)
        progress.apply_review(True)
        progress.apply_review(False)
        self.assertEqual(progress.interval, 1)
        self.assertEqual(progress.level, 0)
        self.assertFalse(progress.is_known)

    def test_streak_counts_one_day_once(self):
        stats = UserStats.get_stats(self.user)
        stats.update_streak()
        stats.update_streak()
        self.assertEqual(stats.current_streak, 1)
        self.assertEqual(stats.total_reviews, 2)


class ListManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('owner', password='swordfish-42')
        self.other = User.objects.create_user('other', password='swordfish-42')
        self.deck = make_list(owner=self.user, name='Mine')

    def test_owner_can_toggle_visibility(self):
        self.client.force_login(self.user)
        self.client.post(reverse('toggle_public', args=[self.deck.id]))
        self.deck.refresh_from_db()
        self.assertFalse(self.deck.is_public)

    def test_a_stranger_cannot_delete_someone_elses_list(self):
        self.client.force_login(self.other)
        self.client.post(reverse('delete_list', args=[self.deck.id]))
        self.assertTrue(WordList.objects.filter(id=self.deck.id).exists())

    def test_owner_can_delete_their_list(self):
        self.client.force_login(self.user)
        self.client.post(reverse('delete_list', args=[self.deck.id]))
        self.assertFalse(WordList.objects.filter(id=self.deck.id).exists())

    def test_joining_by_code_adds_the_list(self):
        friend_deck = make_list(owner=self.other, name='Friend', public=False)
        self.client.force_login(self.user)
        self.client.post(reverse('dashboard'), {'action': 'join', 'code': friend_deck.share_code})
        self.assertTrue(JoinedList.objects.filter(user=self.user, word_list=friend_deck).exists())

    def test_a_bad_code_reports_an_error(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('dashboard'), {'action': 'join', 'code': 'ZZZZZZ'})
        self.assertContains(response, 'No list found with that code.')

    def test_share_codes_are_unique(self):
        codes = {make_list(owner=self.user).share_code for _ in range(10)}
        self.assertEqual(len(codes), 10)
