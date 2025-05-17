from django.core.management.base import BaseCommand
import os
import sys

class Command(BaseCommand):
    """
    Management command to toggle between development mode and prelaunch mode.
    
    Usage:
        python manage.py toggle_prelaunch       # Show current status
        python manage.py toggle_prelaunch --on  # Set prelaunch mode on (DEVELOPMENT=False)
        python manage.py toggle_prelaunch --off # Set prelaunch mode off (DEVELOPMENT=True)
        
    This command modifies the DEVELOPMENT environment variable in memory and displays
    the current state.
    """
    
    help = 'Toggle between development mode and prelaunch mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--on',
            action='store_true',
            help='Force prelaunch mode on (DEVELOPMENT=False)',
        )
        parser.add_argument(
            '--off',
            action='store_true',
            help='Force prelaunch mode off (DEVELOPMENT=True)',
        )

    def handle(self, *args, **options):
        force_on = options.get('on', False)
        force_off = options.get('off', False)
        
        # Ensure both flags aren't used together
        if force_on and force_off:
            self.stdout.write(self.style.ERROR('Error: Cannot use both --on and --off flags together.'))
            return
        
        # Print current state
        from django.conf import settings
        
        try:
            development_mode = settings.DEVELOPMENT
            current_status = "OFF" if not development_mode else "ON"
            self.stdout.write(f"Current prelaunch mode is: {current_status} (DEVELOPMENT={development_mode})")
            
            # If forcing a state, show what it would be (not actually changing it)
            if force_on:
                self.stdout.write(self.style.SUCCESS(
                    f"To enable prelaunch mode (DEVELOPMENT=False), set DEVELOPMENT to 'False' in your environment variables."
                ))
            elif force_off:
                self.stdout.write(self.style.SUCCESS(
                    f"To disable prelaunch mode (DEVELOPMENT=True), set DEVELOPMENT to 'True' in your environment variables."
                ))
            else:
                # Toggle mode instructions
                new_value = not development_mode
                new_status = "OFF" if not new_value else "ON"
                self.stdout.write(self.style.SUCCESS(
                    f"To toggle to {new_status} prelaunch mode, set DEVELOPMENT to '{new_value}' in your environment variables."
                ))
                
            # Render specific instructions
            self.stdout.write("\nOn Render.com:")
            self.stdout.write("1. Go to your service dashboard")
            self.stdout.write("2. Click 'Environment' tab")
            self.stdout.write("3. Add or update the DEVELOPMENT environment variable")
            self.stdout.write("4. Redeploy your service for changes to take effect")
            
        except AttributeError:
            self.stdout.write(self.style.ERROR(
                "Could not detect DEVELOPMENT setting. Please ensure it's defined in your settings.py."
            ))