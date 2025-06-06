from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, authenticate
from .models import Project, Feedback, Notification, FeedbackRequest, FeedbackReaction, Profile, Tag, Badge, UserBadge, ProjectImage, WaitlistEntry
from .forms import ProjectForm, FeedbackForm, SignUpForm, ProfileUpdateForm, UserUpdateForm, ProjectImageFormSet, WaitlistForm
from .utils import (
    create_feedback_notification, 
    create_liked_feedback_notification, 
    create_reaction_notification,
    get_user_notifications, 
    get_unread_notification_count, 
    get_time_ago,
    check_and_award_badges,
    get_user_badges
)
from django.db.models import Count, Q, F, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.conf import settings
from .analytics import track_feedback_given, track_project_created, track_waitlist_signup, track_homepage_view, track_signup

def home(request):
    """Home page view."""
    # Track homepage view if analytics is enabled
    if settings.ENABLE_ANALYTICS:
        track_homepage_view(request)
    
    # If in development mode, show the regular home page
    if not settings.DEVELOPMENT:
        # Get stats for homepage
        total_projects_count = Project.objects.count()
        total_feedback_count = Feedback.objects.count()
        active_voters_count = User.objects.filter(given_feedback__isnull=False).distinct().count()
        
        return render(request, 'core/home.html', {
            'total_projects_count': total_projects_count,
            'total_feedback_count': total_feedback_count,
            'active_voters_count': active_voters_count
        })
    else:
        # In production, show the waitlist landing page
        return waitlist_landing_page(request)

def waitlist_landing_page(request):
    """Landing page with waitlist signup form."""
    if request.method == 'POST':
        form = WaitlistForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            # Check if this email is already on the waitlist
            if WaitlistEntry.objects.filter(email=email).exists():
                messages.info(request, "You're already on our waitlist! We'll notify you when we launch.")
            else:
                form.save()
                messages.success(request, "Thanks for joining our waitlist! We'll notify you when we launch.")
            return redirect('waitlist')
    else:
        form = WaitlistForm()
    
    return render(request, 'core/waitlist_landing.html', {'form': form})

def signup(request):
    """User registration view."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # User is automatically created with a profile due to signal
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            
            # Track signup if analytics is enabled
            if settings.ENABLE_ANALYTICS:
                track_signup(request, user)
            
            messages.success(request, 'Account created successfully! You now have 1 credit to start.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def profile(request):
    """User profile view."""
    username = request.GET.get('username')
    
    if username and username != request.user.username:
        # View another user's profile
        profile_user = get_object_or_404(User, username=username)
        is_own_profile = False
    else:
        # View own profile
        profile_user = request.user
        is_own_profile = True
    
    user_projects = Project.objects.filter(owner=profile_user).order_by('-created_at')
    received_feedback = Feedback.objects.filter(project__owner=profile_user).order_by('-created_at')
    given_feedback = Feedback.objects.filter(giver=profile_user).order_by('-created_at')
    
    # Get feedback requests for user's projects
    feedback_requests = FeedbackRequest.objects.filter(project__owner=profile_user).order_by('-created_at')
    
    # Get user badges
    user_badges = get_user_badges(profile_user)
    
    # Only get notifications for own profile
    user_notifications = get_user_notifications(request.user, limit=5) if is_own_profile else None
    
    context = {
        'profile_user': profile_user,
        'user_projects': user_projects,
        'received_feedback': received_feedback,
        'given_feedback': given_feedback,
        'feedback_requests': feedback_requests,
        'user_notifications': user_notifications,
        'is_own_profile': is_own_profile,
        'user_badges': user_badges,
    }
    return render(request, 'core/profile.html', context)

def top_projects(request):
    """View to display top projects by votes."""
    # Get all projects count for the stats
    total_projects_count = Project.objects.count()
    
    # Get total feedback count
    total_feedback_count = Feedback.objects.count()
    
    # Get count of users who have given feedback
    active_voters_count = User.objects.filter(given_feedback__isnull=False).distinct().count()
    
    # Get top projects by vote count
    top_projects = Project.objects.annotate(
        feedback_count=Count('feedback')
    ).order_by('-total_votes')[:12]
    
    return render(request, 'core/top_projects.html', {
        'top_projects': top_projects,
        'total_projects_count': total_projects_count,
        'total_feedback_count': total_feedback_count,
        'active_voters_count': active_voters_count
    })

@login_required
def submit_project(request):
    """Submit a new project."""
    

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            # Create project but don't save to DB yet
            project = form.save(commit=False)
            project.owner = request.user
            project.is_active = True
            project.save()
            
            # Process tags (save_m2m is needed for ManyToMany fields)
            form.save_m2m()
            
            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            for i, img in enumerate(additional_images):
                ProjectImage.objects.create(
                    project=project,
                    image=img,
                    order=i
                )
            
            # Check and award badges
            check_and_award_badges(request.user)
            
            messages.success(request, 'Project submitted successfully! Use credits to get feedback.')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'core/submit_project.html', {'form': form})

@login_required
def update_project(request, pk):
    """Update an existing project."""
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user is the owner
    if request.user != project.owner:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('project_detail', pk=project.id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            
            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            for i, img in enumerate(additional_images):
                ProjectImage.objects.create(
                    project=project,
                    image=img,
                    order=project.images.count() + i  # Append to existing images
                )
            
            messages.success(request, 'Project updated successfully!')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'core/submit_project.html', {
        'form': form,
        'is_update': True,
        'project': project,
        'project_images': project.images.all()
    })

@login_required
def project_detail(request, pk):
    """View project details."""
    project = get_object_or_404(Project, pk=pk)
    feedback_list = Feedback.objects.filter(project=project)
    
    # Increment view count for all viewers
    project.increment_view_count()
    
    # Handle toggle_active if POST request
    if request.method == 'POST' and 'toggle_active' in request.POST:
        # Ensure only the owner can toggle active status
        if request.user == project.owner:
            project.toggle_active()
            status = "activated" if project.is_active else "deactivated"
            messages.success(request, f"Project {status} successfully.")
        else:
            messages.error(request, "You don't have permission to perform this action.")
        return redirect('project_detail', pk=project.id)
    
    context = {
        'project': project,
        'feedback_list': feedback_list,
    }
    return render(request, 'core/project_detail.html', context)

@login_required
def feedback_dashboard(request):
    """Dashboard to choose a project to give feedback on."""
    # Find projects with unfulfilled feedback requests that this user hasn't given feedback on yet
    
    # Get projects with pending feedback requests
    query_filter = Q(is_active=True) & ~Q(owner=request.user) & Q(
        feedback_requests__fulfilled_count__lt=F('feedback_requests__requested_count')
    )
    
    projects_with_pending_requests = Project.objects.filter(query_filter).annotate(
        # Check if user has already given feedback
        user_has_given_feedback=Count('feedback', filter=Q(feedback__giver=request.user)),
        # Calculate remaining feedback slots
        pending_count=Subquery(
            FeedbackRequest.objects.filter(
                project=OuterRef('pk')
            ).order_by('-created_at').values('requested_count')[:1],
            output_field=IntegerField()
        ) - Subquery(
            FeedbackRequest.objects.filter(
                project=OuterRef('pk')
            ).order_by('-created_at').values('fulfilled_count')[:1],
            output_field=IntegerField()
        )
    ).filter(
        # Exclude projects user has already given feedback to
        user_has_given_feedback=0,
        # Only include projects with pending feedback slots
        pending_count__gt=0
    ).order_by('?')[:3]  # Get up to 3 random projects
    
    # If we don't have 3 projects with pending requests, get some random active projects
    if projects_with_pending_requests.count() < 3:
        needed_count = 3 - projects_with_pending_requests.count()
        # Get random active projects, excluding ones user owns or has already given feedback to
        random_projects = Project.objects.filter(
            is_active=True
        ).exclude(
            owner=request.user
        ).exclude(
            id__in=projects_with_pending_requests.values_list('id', flat=True)
        ).exclude(
            feedback__giver=request.user
        ).order_by('?')[:needed_count]
        
        # Combine the two querysets
        projects_to_show = list(projects_with_pending_requests) + list(random_projects)
    else:
        projects_to_show = projects_with_pending_requests
    
    context = {
        'random_projects': projects_to_show,
    }
    return render(request, 'core/feedback_dashboard.html', context)

@login_required
def give_feedback(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Prevent users from giving feedback to their own projects
    if project.owner == request.user:
        messages.error(request, "You cannot give feedback to your own project.")
        return redirect('feedback_dashboard')
    
    # Check if user has already given feedback to this project
    if Feedback.objects.filter(project=project, giver=request.user).exists():
        messages.error(request, "You have already provided feedback for this project.")
        return redirect('feedback_dashboard')
        
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.project = project
            feedback.giver = request.user
            
            # Get vote type from form
            vote_type = request.POST.get('vote_type', 'none')
            if vote_type in ['up', 'down', 'none']:
                feedback.vote_type = vote_type
            
            feedback.save()
            
            
            # Create notification for project owner
            create_feedback_notification(feedback)
            
            # Find the most recent unfulfilled feedback request for this project and increment its count
            feedback_request = FeedbackRequest.objects.filter(
                project=project,
                fulfilled_count__lt=F('requested_count')
            ).order_by('-created_at').first()
            
            if feedback_request:
                feedback_request.increment_fulfilled()
            
            # Award credit to feedback giver
            profile = request.user.profile
            profile.credits += 1
            profile.save()
            
            # Check and award badges
            check_and_award_badges(request.user)
            
            messages.success(request, "Thank you for your feedback! You've gained 1 credit.")
            return redirect(reverse('profile') + '?active_tab=given_feedback')
    else:
        form = FeedbackForm()
    
    return render(request, 'core/give_feedback.html', {
        'project': project,
        'form': form,
    })

@login_required
def like_feedback(request, feedback_id):
    """Like a feedback and award a credit to the giver."""
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    # Only project owner can like feedback
    if request.user != feedback.project.owner:
        messages.warning(request, 'Only the project owner can like feedback.')
        return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
    
    # Prevent liking already liked feedback
    if feedback.is_liked:
        messages.warning(request, 'You have already liked this feedback.')
        return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
    
    # Set feedback as liked and award credit to giver
    feedback.is_liked = True
    feedback.save()
    
    # Add credit to project owner
    owner_profile = feedback.project.owner.profile
    owner_profile.credits += 1
    owner_profile.save()
    
    # Create notification for feedback giver
    create_liked_feedback_notification(feedback)
    
    # Award credit to feedback giver (will be implemented in models)
    feedback.award_credit()
    
    # Check and award badges for the feedback giver
    check_and_award_badges(feedback.giver)
    
    messages.success(request, 'Feedback liked and credit awarded to the giver.')
    return redirect(reverse('profile') + '?active_tab=received_feedback')

@login_required
def react_to_feedback(request, feedback_id):
    """React to feedback with emoji reaction and optional follow-up note."""
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    # Only project owner can react to feedback
    if request.user != feedback.project.owner:
        messages.warning(request, 'Only the project owner can react to feedback.')
        return HttpResponseRedirect(reverse('feedback_detail', args=[feedback.project.id, feedback.id]))
    
    if request.method == 'POST':
        reaction_type = request.POST.get('reaction_type')
        follow_up_note = request.POST.get('follow_up_note', '').strip()
        
        # Validate reaction type
        valid_reaction_types = [choice[0] for choice in FeedbackReaction.REACTION_CHOICES]
        
        if reaction_type not in valid_reaction_types:
            messages.error(request, 'Invalid reaction type.')
            return HttpResponseRedirect(reverse('feedback_detail', args=[feedback.project.id, feedback.id]))
        
        # Create or update reaction
        reaction, created = FeedbackReaction.objects.update_or_create(
            feedback=feedback,
            defaults={
                'reaction_type': reaction_type,
                'follow_up_note': follow_up_note if follow_up_note else None
            }
        )
        
        # If this is a new reaction, mark the feedback as liked to maintain backward compatibility
        if created and not feedback.is_liked:
            feedback.is_liked = True
            feedback.save()
            
            # Create notification for feedback giver
            create_reaction_notification(reaction)
            
            # Award credit to feedback giver
            feedback.award_credit()
            
            # Check and award badges for the feedback giver
            check_and_award_badges(feedback.giver)
            
            # Add credit to project owner (maintain backward compatibility)
            owner_profile = feedback.project.owner.profile
            owner_profile.credits += 1
            owner_profile.save()
        # If the reaction is updated, send a new notification
        else:
            create_reaction_notification(reaction)
        
        reaction_display = dict(FeedbackReaction.REACTION_CHOICES)[reaction_type]
        messages.success(request, f'You reacted with {reaction_display} to this feedback.')
        
    return redirect(reverse('profile') + '?active_tab=received_feedback')

@login_required
def report_feedback(request, feedback_id):
    """Report inappropriate or low-quality feedback."""
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    # Only project owner can report feedback
    if request.user != feedback.project.owner:
        messages.warning(request, 'Only the project owner can report feedback.')
        return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
    
    # Check if feedback has already been reported
    if feedback.is_reported:
        messages.info(request, 'This feedback has already been reported.')
        return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
    
    if request.method == 'POST':
        # Get report reason from the form
        report_reason = request.POST.get('report_reason', '')
        
        if report_reason.strip():
            # Mark feedback as reported
            feedback.is_reported = True
            feedback.report_reason = report_reason
            feedback.save()
            
            messages.success(request, 'Feedback reported for review. An administrator will review your report shortly.')
            return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
        else:
            messages.error(request, 'Please provide a reason for reporting this feedback.')
    
    # For GET requests or invalid POST requests, show the report form
    return render(request, 'core/report_feedback.html', {'feedback': feedback})


@login_required
def get_feedback(request, project_id, credits):
    """Get feedback for a project."""
    project = get_object_or_404(Project, id=project_id)
    
    # Convert credits to integer to ensure proper data type
    try:
        credits = int(credits)
        # Ensure credits is a positive number
        if credits <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Number of credits must be positive.'}, status=400)
            messages.error(request, "Number of credits must be positive.")
            return redirect('profile')
    except (ValueError, TypeError):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid credit amount.'}, status=400)
        messages.error(request, "Invalid credit amount.")
        return redirect('profile')
    
    # Check if user is the project owner
    if request.user != project.owner:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'You can only get feedback for your own projects.'}, status=403)
        messages.error(request, "You can only get feedback for your own projects.")
        return redirect('profile')
    
    # Check if user has enough credits
    owner_profile = project.owner.profile
    if owner_profile.credits < credits:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'You don\'t have enough credits to request feedback.'}, status=400)
        messages.error(request, "You don't have enough credits to request feedback.")
        return redirect('profile')
    
    # Deduct the specified number of credits
    owner_profile.credits -= credits
    owner_profile.save()
    
    # Create a feedback request entry to track the requested feedback
    feedback_request = FeedbackRequest.objects.create(
        project=project,
        requested_count=credits
    )
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get current feedback count for the message
        current_feedback_count = project.get_feedback_count()
        feedback_message = f'You will get {credits} more feedback for your project soon!' if current_feedback_count > 0 else f'You will get {credits} feedback for your project soon!'
        
        return JsonResponse({
            'success': True,
            'message': feedback_message,
            'credits': owner_profile.credits,
            'current_feedback_count': current_feedback_count,
            'request_id': feedback_request.id  # Include the request ID for tracking
        })
    
    # Handle regular request    
    messages.success(request, f"You will get {credits} feedback(s) for your project soon!")
    return redirect(reverse('profile') + '?active_tab=feedback_requests')

@login_required
def get_feedback_page(request, project_id):
    """Display the page for customizing and requesting feedback."""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the project owner
    if request.user != project.owner:
        messages.error(request, "You can only request feedback for your own projects.")
        return redirect('profile')
    
    # Render the get feedback form
    return render(request, 'core/get_feedback.html', {
        'project': project,
    })

@login_required
def request_feedback(request, project_id):
    """Process a feedback request with customized options."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST requests are allowed.'}, status=405)
    
    # Get the project
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the project owner
    if request.user != project.owner:
        return JsonResponse({'success': False, 'message': 'You can only request feedback for your own projects.'}, status=403)
    
    # Get form data
    try:
        credits = int(request.POST.get('credits', 0))
        priority = request.POST.get('priority', 'standard')
        
        # Parse feedback types JSON
        import json
        feedback_types = json.loads(request.POST.get('feedback_types', '[]'))
        
        # Get feedback prompt if provided
        feedback_prompt = request.POST.get('feedback_prompt', '').strip() or None
        
        # Ensure at least one feedback type is selected
        if not feedback_types:
            return JsonResponse({'success': False, 'message': 'Please select at least one feedback type.'}, status=400)
        
        # Validate credits amount
        if credits <= 0:
            return JsonResponse({'success': False, 'message': 'Number of credits must be positive.'}, status=400)
            
        # Check if user has enough credits
        owner_profile = project.owner.profile
        if owner_profile.credits < credits:
            return JsonResponse({'success': False, 'message': 'You don\'t have enough credits to request feedback.'}, status=400)
        
        # Update project's feedback types
        project.feedback_type_wanted = feedback_types
        project.save()
        
        # Deduct the specified number of credits
        owner_profile.credits -= credits
        owner_profile.save()
        
        # Create a feedback request entry with priority flag and feedback types
        feedback_request = FeedbackRequest.objects.create(
            project=project,
            requested_count=credits,
            priority=priority == 'high',  # Store priority as boolean
            feedback_prompt=feedback_prompt,
            feedback_type_wanted=feedback_types  # Store feedback types in the request
        )
        
        # Get current feedback count for the message
        current_feedback_count = project.get_feedback_count()
        priority_text = "high priority " if priority == 'high' else ""
        feedback_message = f'You will get {credits} {priority_text}feedback for your project soon!'
        
        return JsonResponse({
            'success': True,
            'message': feedback_message,
            'credits': owner_profile.credits,
            'current_feedback_count': current_feedback_count,
            'request_id': feedback_request.id
        })
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'message': f'Invalid request data: {str(e)}'}, status=400)

@login_required
def get_notification_count(request):
    """API endpoint to get notification count"""
    count = get_unread_notification_count(request.user)
    return JsonResponse({'count': count})

@login_required
def user_notifications(request):
    """View to display user notifications"""
    # Get notification type filter
    notification_type = request.GET.get('type')
    
    # Apply filter if specified
    if notification_type and notification_type != 'all':
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type=notification_type
        ).order_by('-created_at')[:50]
    else:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:50]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        data = [
            {
                'id': n.id,
                'message': n.message,
                'type': n.notification_type,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
                'time_ago': get_time_ago(n.created_at),
                'is_viewed': n.is_viewed,
            } for n in notifications
        ]
        return JsonResponse({'notifications': data})
    
    # Mark all notifications as read
    if Notification.objects.filter(recipient=request.user, is_viewed=False).exists():
        print("Marking all notifications as read")
        mark_all_notifications_read(request)
    
    # Render notifications page for non-AJAX requests
    return render(request, 'core/user_notifications.html', {'notifications': notifications})

@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Mark notification as viewed
    if not notification.is_viewed:
        notification.is_viewed = True
        notification.save()
    
    # Redirect based on notification type
    if notification.feedback:
        # Redirect to the feedback detail page
        return redirect('feedback_detail', project_id=notification.feedback.project.id, feedback_id=notification.feedback.id)
    elif notification.notification_type == 'badge_earned':
        # Redirect to the profile page
        return redirect('profile')
    
    # If no specific redirect, go to notifications page
    return redirect('user_notifications')

@login_required
def mark_all_notifications_read(request):
    """Mark all user notifications as read."""
    
    Notification.objects.filter(recipient=request.user, is_viewed=False).update(is_viewed=True)
    messages.success(request, "All notifications marked as read.")
    
    # Redirect back to notifications page
    return redirect('user_notifications')

@login_required
def feedback_detail(request, feedback_id, project_id):
    """View detailed feedback information."""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    project = feedback.project
    
    # Check permissions - only project owner and feedback giver can view details
    if request.user != project.owner and request.user != feedback.giver:
        messages.error(request, "You don't have permission to view this feedback.")
        return redirect('home')
    
    # Calculate time spent 
    # For now we'll just show the creation time, but in a future update
    # we could track the actual time spent writing feedback
    
    # Mark notification as viewed if it exists
    if request.user == project.owner:
        Notification.objects.filter(
            recipient=request.user,
            feedback=feedback,
            is_viewed=False
        ).update(is_viewed=True)
    
    # Get the feedback request associated with this feedback (based on creation time)
    feedback_request = FeedbackRequest.objects.filter(
        project=project,
        created_at__lte=feedback.created_at
    ).order_by('-created_at').first()
    
    # Get feedback reaction if exists
    reaction = None
    try:
        if hasattr(feedback, 'reactions'):
            reaction = feedback.reactions.first()
    except:
        reaction = None
    
    context = {
        'feedback': feedback,
        'project': project,
        'is_owner': request.user == project.owner,
        'is_giver': request.user == feedback.giver,
        'feedback_request': feedback_request,
        'feedback_reaction': reaction,
    }
    
    return render(request, 'core/feedback_detail.html', context)

@login_required
def edit_profile(request):
    """Edit user profile view."""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'core/edit_profile.html', context)

@login_required
def delete_project(request, pk):
    """Delete a project."""
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user is the owner
    if request.user != project.owner:
        messages.error(request, "You don't have permission to delete this project.")
        return redirect('profile')
    
    if request.method == 'POST':
        # Store project title for success message
        project_title = project.title
        
        # Delete the project
        project.delete()
        
        messages.success(request, f'"{project_title}" has been deleted successfully.')
        return redirect('profile')
    
    # GET request shows confirmation page
    return render(request, 'core/delete_project.html', {'project': project})

def login_view(request):
    """Custom login view to check for banned users."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is banned
            if hasattr(user, 'profile') and user.profile.is_banned:
                messages.error(request, "Your account has been banned. Please contact the administrators for assistance.")
                return render(request, 'registration/login.html')
            
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'registration/login.html')

@login_required
def review_preparation(request, project_id):
    """
    View for review preparation page before giving feedback
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Get the latest feedback request for this project
    feedback_request = FeedbackRequest.objects.filter(
        project=project,
        fulfilled_count__lt=F('requested_count')
    ).order_by('-created_at').first()
    
    return render(request, 'core/review_preparation.html', {
        'project': project,
        'feedback_request': feedback_request
    })

def about(request):
    """About page view."""
    # Check if we're in prelaunch mode
    if not settings.DEVELOPMENT:
        # Use a simplified about page in prelaunch mode
        return render(request, 'core/about_prelaunch.html')
    
    # Standard about page in development mode
    return render(request, 'core/about.html')

def privacy_policy(request):
    """Privacy policy page view."""
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    """Terms of service page view."""
    return render(request, 'core/terms_of_service.html')
    
    