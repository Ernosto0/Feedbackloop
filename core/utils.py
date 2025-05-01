from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Notification, Badge, UserBadge, Feedback, Project

# Import email functions if email notifications are enabled
if settings.SEND_EMAIL_NOTIFICATIONS:
    from .emailer import send_feedback_received_email, send_feedback_liked_email

def create_feedback_notification(feedback):
    """Create notification when new feedback is received"""
    project = feedback.project
    recipient = project.owner
    
    # Create in-app notification
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type='feedback_received',
        feedback=feedback,
        message=f"You received new feedback on your project '{project.title}' from {feedback.giver.username}."
    )
    
    # Send email notification if enabled
    if settings.SEND_EMAIL_NOTIFICATIONS and recipient.email:
        print("Sending feedback received email to in notification:", recipient.email)
        try:
            send_feedback_received_email(recipient, feedback)
        except Exception as e:
            # Log the error but don't break the flow
            print(f"Error sending feedback received email: {e}")
    
    return notification

def create_liked_feedback_notification(feedback):
    """Create notification when feedback is liked"""
    recipient = feedback.giver
    
    # Create in-app notification
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type='feedback_liked',
        feedback=feedback,
        message=f"Your feedback on project '{feedback.project.title}' was liked by the project owner. You gained 1 credit."
    )
    
    # Send email notification if enabled
    if settings.SEND_EMAIL_NOTIFICATIONS and recipient.email:
        try:
            send_feedback_liked_email(recipient, feedback)
        except Exception as e:
            # Log the error but don't break the flow
            print(f"Error sending feedback liked email: {e}")
    
    return notification

def create_reaction_notification(reaction):
    """Create notification for feedback reaction with specific reaction type"""
    feedback = reaction.feedback
    recipient = feedback.giver
    reaction_type = reaction.reaction_type
    project_title = feedback.project.title
    
    # Set notification type and message based on reaction type
    if reaction_type == 'helpful':
        notification_type = 'feedback_helpful'
        message = f"The owner marked your feedback on '{project_title}' as helpful. ❤️"
    elif reaction_type == 'thanks':
        notification_type = 'feedback_thanks'
        message = f"The owner thanked you for your feedback on '{project_title}'. 🙏"
    elif reaction_type == 'considering':
        notification_type = 'feedback_considering'
        message = f"The owner is considering your feedback on '{project_title}'. 💡"
    else:
        notification_type = 'feedback_liked'
        message = f"Your feedback on '{project_title}' was liked by the project owner."
    
    # Add note info if there's a follow-up note
    if reaction.follow_up_note:
        message += f" Note: \"{reaction.follow_up_note}\""
    
    # Add credit info
    message += " You gained 1 credit."
    
    # Create in-app notification
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        feedback=feedback,
        reaction=reaction,
        message=message
    )
    
    # Send email notification if enabled (still use the liked email for now)
    if settings.SEND_EMAIL_NOTIFICATIONS and recipient.email:
        try:
            send_feedback_liked_email(recipient, feedback)
        except Exception as e:
            # Log the error but don't break the flow
            print(f"Error sending feedback reaction email: {e}")
    
    return notification

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

def check_and_award_badges(user):
    """Check if user qualifies for any badges and award them"""
    # Get counts for each achievement type
    feedback_given_count = Feedback.objects.filter(giver=user).count()
    feedback_liked_count = Feedback.objects.filter(giver=user, is_liked=True).count()
    projects_submitted_count = Project.objects.filter(owner=user).count()
    
    # Get badges that the user doesn't have yet
    awarded_badge_ids = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    
    # Check feedback given badges
    feedback_given_badges = Badge.objects.filter(
        badge_type='feedback_given',
        required_count__lte=feedback_given_count
    ).exclude(id__in=awarded_badge_ids)
    
    # Check feedback liked badges
    feedback_liked_badges = Badge.objects.filter(
        badge_type='feedback_liked',
        required_count__lte=feedback_liked_count
    ).exclude(id__in=awarded_badge_ids)
    
    # Check projects submitted badges
    projects_submitted_badges = Badge.objects.filter(
        badge_type='projects_submitted',
        required_count__lte=projects_submitted_count
    ).exclude(id__in=awarded_badge_ids)
    
    # Award all new badges
    new_badges = []
    for badge in list(feedback_given_badges) + list(feedback_liked_badges) + list(projects_submitted_badges):
        user_badge = UserBadge.objects.create(user=user, badge=badge)
        new_badges.append(badge)
        
        # Create notification for the new badge
        Notification.objects.create(
            recipient=user,
            notification_type='badge_earned',
            message=f"Congratulations! You've earned the '{badge.name}' badge: {badge.description}"
        )
    
    return new_badges

def get_user_badges(user):
    """Get all badges for a user"""
    return UserBadge.objects.filter(user=user) 