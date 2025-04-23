from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, authenticate
from .models import Project, Feedback
from .forms import ProjectForm, FeedbackForm, SignUpForm

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
    
    context = {
        'user_projects': user_projects,
        'received_feedback': received_feedback,
        'given_feedback': given_feedback,
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
            
            messages.success(request, 'Project submitted successfully! You spent 1 credit.')
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
            
            # Deduct credit from user
            profile = request.user.profile
            profile.credits += 1
            profile.save()
            
            # Add credit to project owner
            # owner_profile = project.owner.profile
            # owner_profile.credits += 1
            # owner_profile.save()
            
            messages.success(request, "Thank you for your feedback! You've used 1 credit.")
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
def get_feedback(request, project_id):
    """Get feedback for a project."""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the project owner
    if request.user != project.owner:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'You can only get feedback for your own projects.'}, status=403)
        messages.error(request, "You can only get feedback for your own projects.")
        return redirect('profile')
    
    # Check if user has enough credits
    owner_profile = project.owner.profile
    if owner_profile.credits < 1:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'You don\'t have enough credits to request feedback.'}, status=400)
        messages.error(request, "You don't have enough credits to request feedback.")
        return redirect('profile')
    
    # Check if project already has feedback
    if project.get_feedback_count() > 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'This project already has feedback.'}, status=400)
        messages.error(request, "This project already has feedback.")
        return redirect('profile')
    
    # remove 1 credit to project owner to get feedback
    owner_profile.credits -= 1
    owner_profile.save()
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'You will get feedback for your project soon!',
            'credits': owner_profile.credits
        })
    
    # Handle regular request    
    messages.success(request, "You will get feedback for your project soon!")
    return redirect('profile')
    
    