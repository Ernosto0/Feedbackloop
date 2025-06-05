from django.conf import settings
from core.utils import get_unread_notification_count

def notification_context(request):
    """Provide notification count to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        context['unread_notification_count'] = get_unread_notification_count(request.user)
    
    return context

def settings_context(request):
    """Provide selected settings to all templates"""
    return {
        'ENABLE_GOOGLE_AUTH': getattr(settings, 'ENABLE_GOOGLE_AUTH', True)
    } 