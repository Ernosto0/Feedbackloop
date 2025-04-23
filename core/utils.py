from django.utils import timezone
from datetime import timedelta
from .models import Notification

def create_feedback_notification(feedback):
    """Create notification when new feedback is received"""
    project = feedback.project
    recipient = project.owner
    
    Notification.objects.create(
        recipient=recipient,
        notification_type='feedback_received',
        feedback=feedback,
        message=f"You received new feedback on your project '{project.title}' from {feedback.giver.username}."
    )

def create_liked_feedback_notification(feedback):
    """Create notification when feedback is liked"""
    recipient = feedback.giver
    
    Notification.objects.create(
        recipient=recipient,
        notification_type='feedback_liked',
        feedback=feedback,
        message=f"Your feedback on project '{feedback.project.title}' was liked by the project owner. You gained 1 credit."
    )

def get_unread_notification_count(user):
    """Get count of unread notifications for a user"""
    return Notification.objects.filter(recipient=user, is_viewed=False).count()

def get_user_notifications(user, limit=10):
    """Get recent notifications for a user"""
    return Notification.objects.filter(recipient=user).order_by('-created_at')[:limit]

def get_time_ago(time):
    """Format time as a human-readable "time ago" string"""
    now = timezone.now()
    diff = now - time
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return time.strftime("%b %d, %Y") 