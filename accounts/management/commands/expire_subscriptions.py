from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Subscription


class Command(BaseCommand):
    help = 'Expire subscriptions that have passed their access period'

    def handle(self, *args, **options):
        expired = Subscription.objects.filter(
            status='active',
            is_one_time_purchase=True,
            current_period_end__lt=timezone.now()
        ).update(status='expired')

        self.stdout.write(
            self.style.SUCCESS(f'Expired {expired} subscription(s)')
        )
