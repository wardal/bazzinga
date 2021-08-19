from django.core.management.base import BaseCommand

from scheduler.scheduler import Scheduler


class Command(BaseCommand):
    help = 'Run Baz scheduler'

    def handle(self, *args, **options):
        Scheduler().run()
        self.stdout.write(self.style.SUCCESS('Scheduler finished successfully.'))
