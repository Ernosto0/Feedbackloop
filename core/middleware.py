from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.urls import reverse
from django.conf import settings
from .analytics import track_page_view

class BannedUserMiddleware:
    """
    Middleware to check if a user is banned and prevent them from accessing protected views.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if the user is authenticated and has a profile
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            # Check if the user is banned
            if request.user.profile.is_banned:
                # Only apply to non-logout requests to prevent redirect loops
                if not request.path.startswith('/accounts/logout'):
                    # Add a message about account ban
                    messages.error(request, "Your account has been banned. Please contact the administrators for assistance.")
                    
                    # Force logout
                    from django.contrib.auth import logout
                    logout(request)
                    
                    # Redirect to home
                    return redirect('home')
        
        response = self.get_response(request)
        return response


class PrelaunchMiddleware:
    """Middleware to redirect all non-waitlist URLs to the waitlist page when in prelaunch mode."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # In production mode (DEVELOPMENT = False), allow all URLs
        if not settings.DEVELOPMENT:
            return self.get_response(request)
            
        # Define allowed URLs during prelaunch
        allowed_paths = [
            '/waitlist/',                  # Waitlist page
            '/admin/',                     # Admin access
            '/static/',                    # Static files
            '/media/',                     # Media files
            '/about/',                     # About page
            '/privacy-policy/',            # Privacy policy
            '/terms-of-service/',          # Terms of service
            '/favicon.ico',                # Favicon
        ]
        
        # Check if the current path is allowed
        is_allowed = False
        for path in allowed_paths:
            if request.path.startswith(path):
                is_allowed = True
                break
        
        # If path is not allowed or is the home page, redirect to waitlist
        if not is_allowed or request.path == '/':
            return redirect('waitlist')
        
        response = self.get_response(request)
        return response 


class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track if analytics is enabled
        if settings.ENABLE_ANALYTICS:
            # Don't track static/media files and admin pages
            if not any([
                request.path.startswith('/static/'),
                request.path.startswith('/media/'),
                request.path.startswith('/admin/'),
                request.path.startswith('/_debug_/'),
            ]):
                # Get the view name from request if available
                view_name = request.resolver_match.view_name if request.resolver_match else request.path
                track_page_view(request, view_name)
        
        return response 