from django.core.management.base import BaseCommand
from core.utils import notify_waitlist

class Command(BaseCommand):
    """
    Management command to send launch notification emails to all waitlist subscribers.
    
    Usage:
        python manage.py notify_waitlist       # Send emails based on current settings
        python manage.py notify_waitlist --force # Send emails even if notifications are disabled
        
    This command will send a launch notification email to all users who signed up
    for the waitlist. It should be run only once when the site is ready to launch.
    
    Make sure to first set your email settings properly in your .env file:
        MAILERSEND_API_KEY=your_api_key
        MAILERSEND_FROM_EMAIL=your_sender_email
        MAILERSEND_REPLY_EMAIL=your_reply_email
    """
    
    help = 'Send launch notification emails to all waitlist subscribers when the site is ready to launch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send even if email notifications are disabled in settings',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Confirm the action since this is a one-time notification
        self.stdout.write(self.style.WARNING(
            'This will send launch notifications to ALL waitlist subscribers. '
            'This should only be done once when the site is ready to launch.'
        ))
        
        confirm = input('Are you sure you want to proceed? [y/N]: ')
        if confirm.lower() != 'y':
            self.stdout.write(self.style.ERROR('Operation cancelled.'))
            return
        
        if force:
            self.stdout.write(self.style.WARNING('Force sending waitlist notifications (ignoring email settings)'))
            from django.conf import settings
            from django.test.utils import override_settings
            
            # Temporarily enable email notifications
            with override_settings(SEND_EMAIL_NOTIFICATIONS=True):
                count = notify_waitlist()
        else:
            count = notify_waitlist()
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} launch notifications'))
        else:
            self.stdout.write(self.style.WARNING(
                'No notifications were sent. This may be because:\n'
                '1. There are no subscribers in the waitlist\n'
                '2. Email notifications are disabled in settings (use --force to override)\n'
                '3. There was an error with the email service (check console for errors)'
            )) 