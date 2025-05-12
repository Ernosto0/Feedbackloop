from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Sets up the Site configuration required for django-allauth'

    def handle(self, *args, **options):
        # Get or create Site with ID 2
        try:
            site = Site.objects.get(id=2)
            site.domain = 'feedbackloop-k2nl.onrender.com'
            site.name = 'FeedbackLoop'
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated existing Site: {site}'))
        except Site.DoesNotExist:
            site = Site.objects.create(
                id=2,
                domain='feedbackloop-k2nl.onrender.com',
                name='FeedbackLoop'
            )
            self.stdout.write(self.style.SUCCESS(f'Created new Site: {site}'))

        # Output all sites for verification
        self.stdout.write('All sites in database:')
        for s in Site.objects.all():
            self.stdout.write(f'  ID: {s.id}, Domain: {s.domain}, Name: {s.name}') 