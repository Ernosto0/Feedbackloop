from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Badge, UserBadge
from core.utils import check_and_award_badges

class Command(BaseCommand):
    help = 'Award test badges to a specific user'

    def handle(self, *args, **options):
        try:
            # Get the user
            user = User.objects.get(username='ernosto2')
            self.stdout.write(f"Found user: {user.username}")

            # Check and award badges automatically
            new_badges = check_and_award_badges(user)
            if new_badges:
                self.stdout.write(self.style.SUCCESS(f"Automatically awarded {len(new_badges)} badges"))
            else:
                self.stdout.write("No new badges awarded automatically")

            # Manually assign specific badges
            feedback_novice = Badge.objects.get(name='Feedback Novice')
            quality_helper = Badge.objects.get(name='Quality Helper')
            project_starter = Badge.objects.get(name='Project Starter')

            # List of badges to assign
            badges_to_assign = [feedback_novice, quality_helper, project_starter]
            
            # Create UserBadge objects
            for badge in badges_to_assign:
                user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Manually awarded badge: {badge.name}"))
                else:
                    self.stdout.write(f"Badge already exists: {badge.name}")

            # Print the badges the user now has
            self.stdout.write(self.style.SUCCESS(f"\nUser {user.username} now has these badges:"))
            for user_badge in UserBadge.objects.filter(user=user):
                self.stdout.write(f"- {user_badge.badge.name}: {user_badge.badge.description}")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User ernesto2 does not exist"))
        except Badge.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Badge not found: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}")) 