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
    view_count = models.IntegerField(default=0)
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
        
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save()

class ProjectImage(models.Model):
    """Additional images for a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='project_photos/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.project.title}"

class Feedback(models.Model):
    """Feedback for a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    
    # Structured feedback sections
    positives = models.TextField(verbose_name="What's good?")
    improvements = models.TextField(verbose_name="What can be improved?")
    suggestions = models.TextField(verbose_name="Additional suggestions", blank=True)
    
    # Voting system
    VOTE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
        ('none', 'No Vote'),
    ]
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES, default='none')
    
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
    
    def update_project_votes(self):
        """Update project total_votes when vote_type changes"""
        old_vote_impact = 0
        new_vote_impact = 0
        
        # Get previous vote impact before save
        if hasattr(self, '_previous_vote_type'):
            if self._previous_vote_type == 'up':
                old_vote_impact = 1
            elif self._previous_vote_type == 'down':
                old_vote_impact = -1
        
        # Get new vote impact
        if self.vote_type == 'up':
            new_vote_impact = 1
        elif self.vote_type == 'down':
            new_vote_impact = -1
        
        # Calculate net change
        net_change = new_vote_impact - old_vote_impact
        
        # Update project votes if there's a change
        if net_change != 0:
            self.project.total_votes += net_change
            self.project.save()
    
    def save(self, *args, **kwargs):
        """Override save to track vote changes"""
        if self.pk:
            # If this is an existing object, get the previous vote_type
            old_feedback = Feedback.objects.get(pk=self.pk)
            self._previous_vote_type = old_feedback.vote_type
        else:
            # New feedback has no previous vote
            self._previous_vote_type = 'none'
        
        # Save the feedback
        super().save(*args, **kwargs)
        
        # Update project votes
        self.update_project_votes()
    
    class Meta:
        # Prevent multiple feedback from the same user on the same project
        unique_together = ('project', 'giver')

class Notification(models.Model):
    """User notifications for feedback events."""
    NOTIFICATION_TYPES = (
        ('feedback_received', 'Feedback Received'),
        ('feedback_liked', 'Feedback Liked'),
        ('feedback_helpful', 'Feedback Marked as Helpful'),
        ('feedback_thanks', 'Feedback Thanked'),
        ('feedback_considering', 'Feedback Being Considered'),
        ('report_approved', 'Report Approved'),      # New type for approved reports
        ('report_dismissed', 'Report Dismissed'),    # New type for dismissed reports
        ('feedback_reported', 'Feedback Reported'),  # New type for feedback givers
        ('user_warning', 'User Warning'),            # New type for user warnings
        ('badge_earned', 'Badge Earned'),            # New type for earned badges
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, null=True, blank=True)
    reaction = models.ForeignKey('FeedbackReaction', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
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
    priority = models.BooleanField(default=False, help_text="Whether this is a high priority request")
    feedback_prompt = models.TextField(blank=True, null=True, help_text="A message from the project owner to guide feedback givers")
    feedback_type_wanted = models.JSONField(default=list, blank=True, null=True, help_text="Types of feedback wanted for this request")
    
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

class Badge(models.Model):
    """Model for achievement badges that users can earn."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="CSS class for the badge icon")
    badge_type = models.CharField(max_length=50, choices=[
        ('feedback_given', 'Feedback Given'),
        ('feedback_liked', 'Feedback Liked'),
        ('projects_submitted', 'Projects Submitted'),
    ])
    required_count = models.PositiveIntegerField(help_text="Number required to earn this badge")
    
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    """Model to track which badges users have earned."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    date_earned = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-date_earned']
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"

class FeedbackReaction(models.Model):
    """Model to track reactions to feedback."""
    REACTION_CHOICES = [
        ('helpful', '❤️ Helpful'),
        ('thanks', '🙏 Thanks!'),
        ('considering', '💡 Considering this'),
    ]
    
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    follow_up_note = models.TextField(blank=True, null=True, help_text="Optional note from the project owner")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('feedback',)  # Only one reaction per feedback
    
    def __str__(self):
        return f"Reaction to feedback #{self.feedback.id}: {self.get_reaction_type_display()}"
