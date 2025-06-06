from mixpanel import Mixpanel
from django.conf import settings
from typing import Dict, Any, Optional

# Initialize Mixpanel client
mp = Mixpanel(settings.MIXPANEL_TOKEN)

def track_event(distinct_id: str, event_name: str, properties: Optional[Dict[str, Any]] = None):
    """
    Track an event in Mixpanel
    """
    
    if not properties:
        properties = {}
    
    try:
        mp.track(distinct_id, event_name, properties)
    except Exception as e:
        if settings.DEBUG:
            print(f"Failed to track event {event_name}: {str(e)}")

def track_homepage_view(request):
    """Track homepage view events"""
    properties = {
        'url': request.get_host(),
        'referrer': request.META.get('HTTP_REFERER', ''),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'is_authenticated': request.user.is_authenticated
    }
    
    distinct_id = str(request.user.id) if request.user.is_authenticated else request.session.session_key
    track_event(distinct_id, 'Homepage View', properties)

def track_signup(request, user):
    """Track when a new user signs up"""
    properties = {
        'username': user.username,
        'email_domain': user.email.split('@')[1] if user.email else None,
        'referrer': request.META.get('HTTP_REFERER', ''),
        'signup_source': 'website'
    }
    track_event(str(user.id), 'User Signup', properties)

def set_user_profile(distinct_id: str, properties: Dict[str, Any]):
    """
    Set or update user profile properties in Mixpanel
    
    Args:
        distinct_id: Unique identifier for the user
        properties: User properties to set/update
    """
    try:
        mp.people_set(distinct_id, properties)
    except Exception as e:
        if settings.DEBUG:
            print(f"Failed to set user profile: {str(e)}")

# Common events
def track_page_view(request, page_name: str, additional_properties: Optional[Dict[str, Any]] = None):
    """Track page view events"""
    properties = {
        'page': page_name,
        'url': request.path,
        'referrer': request.META.get('HTTP_REFERER', ''),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
    
    if additional_properties:
        properties.update(additional_properties)
    
    distinct_id = str(request.user.id) if request.user.is_authenticated else request.session.session_key
    track_event(distinct_id, 'Page View', properties)

def track_feedback_given(request, feedback):
    """Track when feedback is given"""
    properties = {
        'project_id': feedback.project.id,
        'project_title': feedback.project.title,
        'vote_type': feedback.vote_type,
        'feedback_length': len(feedback.content),
    }
    track_event(str(request.user.id), 'Feedback Given', properties)

def track_project_created(request, project):
    """Track when a new project is created"""
    properties = {
        'project_id': project.id,
        'project_title': project.title,
        'has_images': project.images.exists(),
        'tag_count': project.tags.count(),
    }
    track_event(str(request.user.id), 'Project Created', properties)

def track_waitlist_signup(request, email: str):
    """Track waitlist signups"""
    properties = {
        'email': email,
        'source': request.GET.get('source', 'direct'),
    }
    track_event(request.session.session_key, 'Waitlist Signup', properties) 