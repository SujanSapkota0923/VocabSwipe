"""Fill in missing word meanings from the command line.

Useful when the background thread was interrupted, or to run the lookup
deliberately instead of during an upload:

    python manage.py fetch_meanings            # every list still waiting
    python manage.py fetch_meanings --list-id 4
"""

from django.core.management.base import BaseCommand

from vocab.models import WordList
from vocab.tasks import fetch_meanings_for_list


class Command(BaseCommand):
    help = 'Fetch missing meanings for word lists from the dictionary API.'

    def add_arguments(self, parser):
        parser.add_argument('--list-id', type=int, help='Only process this list.')
        parser.add_argument(
            '--pause',
            type=float,
            default=0.5,
            help='Seconds to wait between words (default: 0.5).',
        )

    def handle(self, *args, **options):
        lists = WordList.objects.all()
        if options['list_id']:
            lists = lists.filter(id=options['list_id'])
            if not lists.exists():
                self.stderr.write(f"No list with id {options['list_id']}.")
                return
        else:
            lists = lists.filter(words__meaning_1='').distinct()

        if not lists.exists():
            self.stdout.write('Nothing to do — every word already has a meaning.')
            return

        for word_list in lists:
            self.stdout.write(f'Looking up meanings for "{word_list.name}" (id {word_list.id})…')
            done = fetch_meanings_for_list(
                word_list.id,
                pause=options['pause'],
                progress=lambda i, total: self.stdout.write(f'  {i}/{total}', ending='\r'),
            )
            self.stdout.write(self.style.SUCCESS(f'  {done} word(s) updated.'))
