from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, Profile, Tag
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Creates sample users and projects for testing'

    def handle(self, *args, **kwargs):
        # Create some tags
        tags = [
            'UI/UX', 'Web App', 'Mobile App', 'Landing Page',
            'Dashboard', 'E-commerce', 'Portfolio', 'Blog'
        ]
        
        for tag_name in tags:
            Tag.objects.get_or_create(name=tag_name)
        
        # Create sample users
        usernames = ['alice_dev', 'bob_designer', 'charlie_ux', 'diana_web']
        
        created_users = []
        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.split('_')[0].title(),
                    'last_name': username.split('_')[1].title()
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            created_users.append(user)
            
            # Give each user some initial credits
            profile = user.profile
            profile.credits = random.randint(3, 10)
            profile.save()

        # Create sample projects
        project_titles = [
            'Modern Portfolio Website',
            'E-commerce Dashboard',
            'Social Media App UI',
            'Task Management System',
            'Travel Blog Design',
            'Fitness Tracking App',
            'Restaurant Landing Page',
            'Real Estate Platform'
        ]

        project_descriptions = [
            'A clean and minimalist portfolio website showcasing creative work.',
            'An intuitive dashboard for managing online store operations.',
            'A modern social media interface with focus on user engagement.',
            'A simple yet powerful task management system for teams.',
            'A beautiful travel blog design with focus on photography.',
            'A mobile app for tracking workouts and nutrition.',
            'An elegant landing page for a high-end restaurant.',
            'A comprehensive platform for real estate listings.'
        ]

        # Create projects and assign to random users
        for title, description in zip(project_titles, project_descriptions):
            user = random.choice(created_users)
            project = Project.objects.create(
                owner=user,
                title=title,
                description=description,
                is_active=True,
                created_at=timezone.now(),
                total_votes=random.randint(0, 50),
                view_count=random.randint(10, 200)
            )
            
            # Add random tags to project
            project_tags = random.sample(tags, random.randint(1, 3))
            for tag_name in project_tags:
                tag = Tag.objects.get(name=tag_name)
                project.tags.add(tag)
            
            self.stdout.write(self.style.SUCCESS(f'Created project: {title}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample data')) 