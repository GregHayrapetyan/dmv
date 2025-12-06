from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import EmailOTP
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete expired and used OTP codes from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete OTPs older than this many days (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Delete expired OTPs
        expired_count = EmailOTP.objects.filter(expires_at__lt=timezone.now()).delete()[0]
        
        # Delete old used OTPs
        old_used_count = EmailOTP.objects.filter(
            is_used=True,
            created_at__lt=cutoff_date
        ).delete()[0]
        
        total_deleted = expired_count + old_used_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {total_deleted} OTP codes '
                f'({expired_count} expired, {old_used_count} old used)'
            )
        )
        logger.info(f'Cleaned up {total_deleted} OTP codes')
