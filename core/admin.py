from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from .models import Profile, Project, Feedback, Tag, Notification, FeedbackRequest, Badge, UserBadge, FeedbackReaction, ProjectImage, WaitlistEntry
from .utils import create_feedback_notification

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits', 'warning_count', 'is_banned', 'user_status')
    list_filter = ('is_banned', 'warning_count')
    search_fields = ('user__username', 'user__email')
    actions = ['warn_user', 'ban_user', 'unban_user']
    
    def user_status(self, obj):
        if obj.is_banned:
            return format_html('<span style="color: red; font-weight: bold;">Banned</span>')
        elif obj.warning_count > 2:
            return format_html('<span style="color: orange; font-weight: bold;">At Risk</span>')
        elif obj.warning_count > 0:
            return format_html('<span style="color: yellow; font-weight: bold;">Warned</span>')
        return format_html('<span style="color: green;">Good Standing</span>')
    user_status.short_description = 'Status'
    
    def warn_user(self, request, queryset):
        for profile in queryset:
            if not profile.is_banned:  # Skip banned users
                profile.warning_count += 1
                profile.save()
                
                # Create notification for the user
                Notification.objects.create(
                    recipient=profile.user,
                    notification_type='user_warning',
                    message=f"You've received a warning from the administrators. Your account now has {profile.warning_count} warning(s). Continued violations may result in a ban."
                )
                
                # Auto-ban if warnings reach threshold (e.g., 3)
                if profile.warning_count >= 3:
                    profile.is_banned = True
                    profile.save()
                    
                    Notification.objects.create(
                        recipient=profile.user,
                        notification_type='user_warning',
                        message="Your account has been banned due to multiple violations. Please contact the administrators for further information."
                    )
        
        self.message_user(request, f"{queryset.count()} user(s) warned successfully.", messages.SUCCESS)
    warn_user.short_description = "Issue warning to selected users"
    
    def ban_user(self, request, queryset):
        for profile in queryset:
            if not profile.is_banned:  # Skip already banned users
                profile.is_banned = True
                profile.save()
                
                # Create notification for the user
                Notification.objects.create(
                    recipient=profile.user,
                    notification_type='user_warning',
                    message="Your account has been banned due to violations. Please contact the administrators for further information."
                )
        
        self.message_user(request, f"{queryset.count()} user(s) banned successfully.", messages.SUCCESS)
    ban_user.short_description = "Ban selected users"
    
    def unban_user(self, request, queryset):
        for profile in queryset:
            if profile.is_banned:  # Only unban banned users
                profile.is_banned = False
                profile.save()
                
                # Create notification for the user
                Notification.objects.create(
                    recipient=profile.user,
                    notification_type='user_warning',
                    message="Your account has been unbanned. You can now use the platform again. Please ensure you follow community guidelines."
                )
        
        self.message_user(request, f"{queryset.count()} user(s) unbanned successfully.", messages.SUCCESS)
    unban_user.short_description = "Unban selected users"

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    fields = ('giver', 'created_at', 'is_liked', 'is_reported')
    readonly_fields = ('giver', 'created_at')

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption', 'order')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'tags')
    search_fields = ('title', 'description', 'owner__username')
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)
    inlines = [ProjectImageInline, FeedbackInline]

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('project', 'giver', 'created_at', 'is_liked', 'is_reported', 'report_handled', 'report_action')
    list_filter = ('is_liked', 'is_reported', 'report_handled', 'created_at')
    search_fields = ('project__title', 'giver__username', 'positives', 'improvements', 'suggestions', 'report_reason')
    date_hierarchy = 'created_at'
    actions = ['approve_report', 'dismiss_report', 'warn_and_approve_report']
    readonly_fields = ('report_reason',)
    
    def report_action(self, obj):
        if obj.is_reported and not obj.report_handled:
            return format_html('<span style="color: red; font-weight: bold;">Pending Review</span>')
        elif obj.is_reported and obj.report_handled:
            return format_html('<span style="color: green; font-weight: bold;">Reviewed</span>')
        return ""
    report_action.short_description = 'Report Status'
    
    def approve_report(self, request, queryset):
        """Approve the report and penalize the feedback giver."""
        for feedback in queryset:
            if feedback.is_reported and not feedback.report_handled:
                # Deduct credit from feedback giver
                giver_profile = feedback.giver.profile
                if giver_profile.credits > 0:  # Ensure they don't go negative
                    giver_profile.credits -= 1
                    giver_profile.save()
                
                # Mark the feedback as handled
                feedback.report_handled = True
                feedback.save()
                
                # Notify the project owner (reporter)
                reporter_notification = Notification.objects.create(
                    recipient=feedback.project.owner,
                    notification_type='report_approved',
                    feedback=feedback,
                    message=f"Your report on feedback for '{feedback.project.title}' has been approved. The inappropriate feedback has been actioned."
                )
                
                # Notify the feedback giver
                giver_notification = Notification.objects.create(
                    recipient=feedback.giver,
                    notification_type='feedback_reported',
                    feedback=feedback,
                    message=f"Your feedback on '{feedback.project.title}' has been reported and the report was approved. You have lost 1 credit."
                )
                
        self.message_user(request, f"{queryset.count()} feedback reports approved and handled.", messages.SUCCESS)
    approve_report.short_description = "Approve selected feedback reports"
    
    def dismiss_report(self, request, queryset):
        """Dismiss the report as invalid."""
        for feedback in queryset:
            if feedback.is_reported and not feedback.report_handled:
                # Mark the feedback as handled but keep it active
                feedback.report_handled = True
                feedback.is_reported = False  # Clear the report flag
                feedback.save()
                
                # Notify the project owner (reporter)
                reporter_notification = Notification.objects.create(
                    recipient=feedback.project.owner,
                    notification_type='report_dismissed',
                    feedback=feedback,
                    message=f"Your report on feedback for '{feedback.project.title}' has been reviewed and dismissed."
                )
                
                # Notify the feedback giver
                giver_notification = Notification.objects.create(
                    recipient=feedback.giver,
                    notification_type='report_dismissed',
                    feedback=feedback,
                    message=f"A report on your feedback for '{feedback.project.title}' has been reviewed and dismissed."
                )
                
        self.message_user(request, f"{queryset.count()} feedback reports dismissed.", messages.SUCCESS)
    dismiss_report.short_description = "Dismiss selected feedback reports"
    
    def warn_and_approve_report(self, request, queryset):
        """Approve the report, penalize the feedback giver, and issue a warning."""
        for feedback in queryset:
            if feedback.is_reported and not feedback.report_handled:
                # Get the giver's profile
                giver_profile = feedback.giver.profile
                
                # Deduct credit
                if giver_profile.credits > 0:
                    giver_profile.credits -= 1
                
                # Issue warning
                giver_profile.warning_count += 1
                
                # Auto-ban if warnings reach threshold
                if giver_profile.warning_count >= 3:
                    giver_profile.is_banned = True
                    
                    # Create ban notification
                    Notification.objects.create(
                        recipient=feedback.giver,
                        notification_type='user_warning',
                        message="Your account has been banned due to multiple violations. Please contact the administrators for further information."
                    )
                
                # Save the profile
                giver_profile.save()
                
                # Mark the feedback as handled
                feedback.report_handled = True
                feedback.save()
                
                # Create notifications
                Notification.objects.create(
                    recipient=feedback.project.owner,
                    notification_type='report_approved',
                    feedback=feedback,
                    message=f"Your report on feedback for '{feedback.project.title}' has been approved. The user has received a warning."
                )
                
                Notification.objects.create(
                    recipient=feedback.giver,
                    notification_type='user_warning',
                    feedback=feedback,
                    message=f"Your feedback on '{feedback.project.title}' has been reported and deemed inappropriate. You have received a warning and lost 1 credit. You now have {giver_profile.warning_count} warning(s)."
                )
        
        self.message_user(request, f"{queryset.count()} reports approved with warnings issued.", messages.SUCCESS)
    warn_and_approve_report.short_description = "Approve reports and warn users"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'created_at', 'is_viewed')
    list_filter = ('notification_type', 'is_viewed', 'created_at')
    search_fields = ('recipient__username', 'message')
    date_hierarchy = 'created_at'

@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ('project', 'created_at', 'requested_count', 'fulfilled_count', 'is_fulfilled')
    list_filter = ('created_at',)
    search_fields = ('project__title', 'project__owner__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('is_fulfilled',)
    
    def is_fulfilled(self, obj):
        return obj.is_fulfilled
    is_fulfilled.boolean = True
    is_fulfilled.short_description = "Fulfilled"

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'required_count')
    list_filter = ('badge_type',)
    search_fields = ('name', 'description')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'date_earned')
    list_filter = ('badge__badge_type', 'date_earned')
    search_fields = ('user__username', 'badge__name')
    date_hierarchy = 'date_earned'

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'image', 'order', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('project__title', 'caption')
    date_hierarchy = 'created_at'

admin.site.register(FeedbackReaction)

@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'created_at')
    search_fields = ('email', 'name')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
