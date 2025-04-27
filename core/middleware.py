from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve

class BannedUserMiddleware:
    """
    Middleware to check if a user is banned and prevent them from accessing protected views.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if user is banned (has profile with is_banned=True)
            if hasattr(request.user, 'profile') and request.user.profile.is_banned:
                # Allow access to logout view
                current_url = resolve(request.path_info).url_name
                if current_url != 'logout':
                    messages.error(request, "Your account has been banned. Please contact the administrators for assistance.")
                    # Force logout
                    return redirect('logout')
        
        response = self.get_response(request)
        return response 