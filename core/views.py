from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, authenticate
from .models import Project, Feedback, Notification
from .forms import ProjectForm, FeedbackForm, SignUpForm
from .utils import create_feedback_notification, create_liked_feedback_notification, get_user_notifications, get_unread_notification_count, get_time_ago

def home(request):
    """Home page view."""
    return render(request, 'core/home.html')

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
            messages.success(request, 'Account created successfully! You now have 1 credit to start.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def profile(request):
    """User profile view."""
    user_projects = Project.objects.filter(owner=request.user)
    received_feedback = Feedback.objects.filter(project__owner=request.user)
    given_feedback = Feedback.objects.filter(giver=request.user)
    user_notifications = get_user_notifications(request.user, limit=5)
    
    context = {
        'user_projects': user_projects,
        'received_feedback': received_feedback,
        'given_feedback': given_feedback,
        'user_notifications': user_notifications,
    }
    return render(request, 'core/profile.html', context)

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
            
            messages.success(request, 'Project submitted successfully! Use credits to get feedback.')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'core/submit_project.html', {'form': form})

@login_required
def project_detail(request, pk):
    """View project details."""
    project = get_object_or_404(Project, pk=pk)
    feedback_list = Feedback.objects.filter(project=project)
    
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
    # Get 3 random active projects that are not owned by the current user
    random_projects = Project.objects.filter(is_active=True).exclude(owner=request.user).order_by('?')[:3]
    
    context = {
        'random_projects': random_projects,
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
        messages.error(request, "You have already provided feedback for this project.") # Add a error handling for this at the future.
        return redirect('feedback_dashboard')
        
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.project = project
            feedback.giver = request.user
            feedback.save()
            
            # Create notification for project owner
            create_feedback_notification(feedback)
            
            # Deduct credit from user
            profile = request.user.profile
            profile.credits += 1
            profile.save()
            
            # Add credit to project owner
            # owner_profile = project.owner.profile
            # owner_profile.credits += 1
            # owner_profile.save()
            
            messages.success(request, "Thank you for your feedback! You've gained 1 credit.")
            return redirect('feedback_dashboard')
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
    
    messages.success(request, 'Feedback liked and credit awarded to the giver.')
    return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))

@login_required
def report_feedback(request, feedback_id):
    """Report inappropriate or low-quality feedback."""
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    # Only project owner can report feedback
    if request.user != feedback.project.owner:
        messages.warning(request, 'Only the project owner can report feedback.')
        return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))
    
    # Mark feedback as reported
    feedback.is_reported = True
    feedback.save()
    
    messages.success(request, 'Feedback reported for review.')
    return HttpResponseRedirect(reverse('project_detail', args=[feedback.project.id]))


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
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get current feedback count for the message
        current_feedback_count = project.get_feedback_count()
        feedback_message = f'You will get {credits} more feedback for your project soon!' if current_feedback_count > 0 else f'You will get {credits} feedback for your project soon!'
        
        return JsonResponse({
            'success': True,
            'message': feedback_message,
            'credits': owner_profile.credits,
            'current_feedback_count': current_feedback_count
        })
    
    # Handle regular request    
    messages.success(request, f"You will get {credits} feedback(s) for your project soon!")
    return redirect('profile')

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
        # Redirect to the project to view the feedback
        return redirect('project_detail', pk=notification.feedback.project.id)
    
    # If no specific redirect, go to notifications page
    return redirect('user_notifications')

@login_required
def mark_all_notifications_read(request):
    """Mark all user notifications as read."""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_viewed=False).update(is_viewed=True)
        messages.success(request, "All notifications marked as read.")
    
    # Redirect back to notifications page
    return redirect('user_notifications')
    
    