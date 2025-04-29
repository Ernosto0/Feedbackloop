from django.core.management.base import BaseCommand
from core.models import Badge

class Command(BaseCommand):
    help = 'Creates initial badges for the system'

    def handle(self, *args, **options):
        badges = [
            # Feedback Given badges
            {
                'name': 'Feedback Novice',
                'description': 'Given 5 pieces of feedback to other projects',
                'icon': 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z',
                'badge_type': 'feedback_given',
                'required_count': 5
            },
            {
                'name': 'Feedback Expert',
                'description': 'Given 25 pieces of feedback to other projects',
                'icon': 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z',
                'badge_type': 'feedback_given',
                'required_count': 25
            },
            {
                'name': 'Feedback Master',
                'description': 'Given 50 pieces of feedback to other projects',
                'icon': 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z',
                'badge_type': 'feedback_given',
                'required_count': 50
            },
            
            # Feedback Liked badges
            {
                'name': 'Quality Helper',
                'description': 'Received 5 likes on your feedback',
                'icon': 'M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5',
                'badge_type': 'feedback_liked',
                'required_count': 5
            },
            {
                'name': 'Quality Expert',
                'description': 'Received 25 likes on your feedback',
                'icon': 'M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5',
                'badge_type': 'feedback_liked',
                'required_count': 25
            },
            {
                'name': 'Feedback Guru',
                'description': 'Received 50 likes on your feedback',
                'icon': 'M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5',
                'badge_type': 'feedback_liked',
                'required_count': 50
            },
            
            # Projects Submitted badges
            {
                'name': 'Project Starter',
                'description': 'Submitted 2 projects for feedback',
                'icon': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
                'badge_type': 'projects_submitted',
                'required_count': 2
            },
            {
                'name': 'Project Pioneer',
                'description': 'Submitted 5 projects for feedback',
                'icon': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
                'badge_type': 'projects_submitted',
                'required_count': 5
            },
            {
                'name': 'Project Master',
                'description': 'Submitted 10 projects for feedback',
                'icon': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
                'badge_type': 'projects_submitted',
                'required_count': 10
            }
        ]
        
        created_count = 0
        for badge_data in badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults={
                    'description': badge_data['description'],
                    'icon': badge_data['icon'],
                    'badge_type': badge_data['badge_type'],
                    'required_count': badge_data['required_count']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created badge: {badge.name}'))
            else:
                self.stdout.write(f'Badge already exists: {badge.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} new badges')) 