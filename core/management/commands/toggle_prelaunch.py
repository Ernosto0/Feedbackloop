from django.core.management.base import BaseCommand
import os
import re

class Command(BaseCommand):
    """
    Management command to toggle between development mode and prelaunch mode.
    
    Usage:
        python manage.py toggle_prelaunch       # Toggle between modes
        python manage.py toggle_prelaunch --on  # Force prelaunch mode on (DEVELOPMENT=False)
        python manage.py toggle_prelaunch --off # Force prelaunch mode off (DEVELOPMENT=True)
        
    This command modifies the .env file to toggle the DEVELOPMENT flag, which controls
    whether the site shows the full application or the waitlist landing page.
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
        
        # Find .env file
        env_path = '.env'
        if not os.path.exists(env_path):
            self.stdout.write(self.style.ERROR(f'Error: Could not find .env file in {os.getcwd()}'))
            return
        
        # Read current settings
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check current DEVELOPMENT setting
        dev_match = re.search(r'^DEVELOPMENT\s*=\s*(True|False)', content, re.MULTILINE)
        current_value = None
        
        if dev_match:
            current_value = dev_match.group(1)
            self.stdout.write(f'Current prelaunch status: {"OFF" if current_value == "True" else "ON"}')
        else:
            # Add DEVELOPMENT setting if not found
            self.stdout.write(self.style.WARNING('DEVELOPMENT setting not found in .env. Adding it.'))
            content += '\nDEVELOPMENT=True\n'
            current_value = 'True'
        
        # Determine new value
        if force_on:
            new_value = 'False'
        elif force_off:
            new_value = 'True'
        else:
            # Toggle value
            new_value = 'False' if current_value == 'True' else 'True'
        
        # Replace the value
        if dev_match:
            new_content = re.sub(
                r'^DEVELOPMENT\s*=\s*(True|False)',
                f'DEVELOPMENT={new_value}',
                content,
                flags=re.MULTILINE
            )
        else:
            new_content = content
        
        # Save the new content
        with open(env_path, 'w') as f:
            f.write(new_content)
        
        # Report status
        mode = "DEVELOPMENT" if new_value == "True" else "PRELAUNCH"
        self.stdout.write(self.style.SUCCESS(
            f'Successfully changed to {mode} mode (DEVELOPMENT={new_value}).\n'
            f'Restart the server for changes to take effect.'
        )) 