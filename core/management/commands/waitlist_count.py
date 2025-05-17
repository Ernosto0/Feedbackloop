from django.core.management.base import BaseCommand
from core.models import WaitlistEntry
from django.utils import timezone

class Command(BaseCommand):
    """
    Management command to show the current waitlist count.
    
    Usage:
        python manage.py waitlist_count       # Shows current count of users on the waitlist
        python manage.py waitlist_count --list # Lists all email addresses on the waitlist
    """
    
    help = 'Display the number of users on the waitlist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all email addresses on the waitlist',
        )

    def handle(self, *args, **options):
        show_list = options.get('list', False)
        
        # Get all waitlist entries
        waitlist_entries = WaitlistEntry.objects.all().order_by('-created_at')
        count = waitlist_entries.count()
        
        # Display the count
        self.stdout.write(self.style.SUCCESS(f'Current waitlist count: {count} users'))
        
        if count == 0:
            return
            
        # Calculate days since the first entry
        if count > 0:
            first_entry = WaitlistEntry.objects.order_by('created_at').first()
            days_active = (timezone.now() - first_entry.created_at).days
            if days_active > 0:
                avg_per_day = count / days_active
                self.stdout.write(f'Waitlist has been active for {days_active} days (avg. {avg_per_day:.2f} signups/day)')
            else:
                self.stdout.write(f'Waitlist started today with {count} signups so far')
        
        # List all email addresses if requested
        if show_list:
            self.stdout.write('\nWaitlist entries:')
            for i, entry in enumerate(waitlist_entries, 1):
                name = f" - {entry.name}" if entry.name else ""
                date = entry.created_at.strftime("%Y-%m-%d %H:%M")
                self.stdout.write(f"{i}. {entry.email}{name} (joined on {date})") 