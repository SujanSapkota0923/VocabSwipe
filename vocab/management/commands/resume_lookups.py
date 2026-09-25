"""Reset meaning lookups that a restart interrupted.

Run at start-up (see start.sh). A list left at "processing" by a killed
worker would otherwise show a progress bar that never moves.
"""

from django.core.management.base import BaseCommand

from vocab.tasks import reset_interrupted_lists


class Command(BaseCommand):
    help = 'Move interrupted meaning lookups back to pending.'

    def handle(self, *args, **options):
        count = reset_interrupted_lists()
        if count:
            self.stdout.write(self.style.SUCCESS(f'Reset {count} interrupted lookup(s).'))
        else:
            self.stdout.write('No interrupted lookups.')
