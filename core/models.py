from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Move PRICING_CHOICES from forms to models
PRICING_CHOICES = [
    ('free', 'Completely Free'),
    ('freemium', 'Freemium (Free tier with paid options)'),
    ('paid', 'Paid Only'),
]

class Profile(models.Model):
    """Extended user profile with feedback credits."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=1)  # Start with 1 credit
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_banned = models.BooleanField(default=False)  # Field to track if user is banned
    warning_count = models.IntegerField(default=0)  # Track warnings given to user
    
    def __str__(self):
        return f"{self.user.username}'s profile"

# Create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Tag(models.Model):
    """Tags for categorizing projects."""
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Project(models.Model):
    """User submitted project."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=100)
    url = models.URLField()
    description = models.TextField()
    photo = models.ImageField(upload_to='project_photos/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    total_votes = models.IntegerField(default=0)
    feedback_type_wanted = models.JSONField(blank=True, null=True, default=list)
    tech_stack = models.CharField(max_length=200, blank=True)
    pricing_plan = models.CharField(max_length=20, choices=PRICING_CHOICES, default='free')
    guest_access_info = models.TextField(blank=True)
    
    def __str__(self):
        return self.title
    
    def toggle_active(self):
        """Toggle project active status."""
        self.is_active = not self.is_active
        self.save()
    
    def get_feedback_count(self):
        """Get the count of feedback received."""
        return self.feedback_set.count()
    
    def get_liked_feedback_count(self):
        """Get the count of liked feedback."""
        return self.feedback_set.filter(is_liked=True).count()
    
    def increment_votes(self):
        """Increment the total votes counter."""
        self.total_votes += 1
        self.save()

class Feedback(models.Model):
    """Feedback for a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    
    # Structured feedback sections
    positives = models.TextField(verbose_name="What's good?")
    improvements = models.TextField(verbose_name="What can be improved?")
    suggestions = models.TextField(verbose_name="Additional suggestions", blank=True)
    
    # Feedback status
    is_liked = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    report_handled = models.BooleanField(default=False)  # Track if a report has been reviewed
    report_reason = models.TextField(blank=True, null=True)  # Optional reason for reporting
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback on {self.project.title} by {self.giver.username}"
    
    def award_credit(self):
        """Award a credit to the feedback giver."""
        if self.is_liked and not self.is_reported:
            profile = self.giver.profile
            profile.credits += 1
            profile.save()
            return True
        return False
    
    class Meta:
        # Prevent multiple feedback from the same user on the same project
        unique_together = ('project', 'giver')

class Notification(models.Model):
    """User notifications for feedback events."""
    NOTIFICATION_TYPES = (
        ('feedback_received', 'Feedback Received'),
        ('feedback_liked', 'Feedback Liked'),
        ('report_approved', 'Report Approved'),      # New type for approved reports
        ('report_dismissed', 'Report Dismissed'),    # New type for dismissed reports
        ('feedback_reported', 'Feedback Reported'),  # New type for feedback givers
        ('user_warning', 'User Warning'),            # New type for user warnings
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_viewed', 'created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:30]}"

class FeedbackRequest(models.Model):
    """Tracks pending feedback requests for projects."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='feedback_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    requested_count = models.PositiveIntegerField(default=1, help_text="Number of feedback slots requested")
    fulfilled_count = models.PositiveIntegerField(default=0, help_text="Number of feedback slots fulfilled")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback request for {self.project.title}: {self.fulfilled_count}/{self.requested_count}"
    
    @property
    def is_fulfilled(self):
        """Check if all requested feedback has been fulfilled."""
        return self.fulfilled_count >= self.requested_count
    
    @property
    def remaining_count(self):
        """Get the number of remaining feedback slots."""
        return max(0, self.requested_count - self.fulfilled_count)
    
    def increment_fulfilled(self):
        """Increment the fulfilled count when feedback is given."""
        if not self.is_fulfilled:
            self.fulfilled_count += 1
            self.save()
            return True
        return False
