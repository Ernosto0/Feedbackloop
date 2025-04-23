from .utils import get_unread_notification_count

def notification_context(request):
    """Add notification count to context for all templates"""
    notification_count = 0
    if request.user.is_authenticated:
        notification_count = get_unread_notification_count(request.user)
    
    return {
        'notification_count': notification_count
    } 