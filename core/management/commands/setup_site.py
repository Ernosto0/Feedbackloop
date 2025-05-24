from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up the site domain for password reset and other functionality'

    def handle(self, *args, **options):
        # Get or create the site with ID 1
        site, created = Site.objects.get_or_create(
            id=settings.SITE_ID,
            defaults={
                'domain': settings.SITE_DOMAIN,
                'name': settings.SITE_NAME
            }
        )

        if not created:
            # Update the existing site
            site.domain = settings.SITE_DOMAIN
            site.name = settings.SITE_NAME
            site.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully {"created" if created else "updated"} site: {site.domain}'
            )
        )

        # Output all sites for verification
        self.stdout.write('All sites in database:')
        for s in Site.objects.all():
            self.stdout.write(f'  ID: {s.id}, Domain: {s.domain}, Name: {s.name}') 