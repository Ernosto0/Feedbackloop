from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from .models import Profile

# This signal already exists in models.py
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

@receiver(post_save, sender=SocialAccount)
def create_profile_for_social_user(sender, instance, created, **kwargs):
    """
    Create a profile for users who sign up via social authentication
    """
    if created:
        user = instance.user
        # Make sure the user doesn't already have a profile
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
            
        # You can extract extra information from social account if needed
        if instance.provider == 'google':
            # Add any google-specific profile setup here if needed
            pass 