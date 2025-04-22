from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
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
    # Check if user already has an active project
    if Project.objects.filter(owner=request.user, is_active=True).exists():
        messages.warning(request, 'You already have an active project. Please deactivate it before submitting a new one.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.is_active = True
            project.save()
            form.save_m2m()  # Save tags
            messages.success(request, 'Project submitted successfully!')
            return redirect('profile')
    else:
        form = ProjectForm()
    
    return render(request, 'core/submit_project.html', {'form': form})

@login_required
def project_detail(request, pk):
    """View project details."""
    project = get_object_or_404(Project, pk=pk)
    feedback_list = Feedback.objects.filter(project=project)
    
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
    """Give feedback to a project."""
    project = get_object_or_404(Project, pk=project_id, is_active=True)
    
    # Prevent users from giving feedback to their own projects
    if project.owner == request.user:
        messages.warning(request, 'You cannot give feedback to your own project.')
        return redirect('feedback_dashboard')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.project = project
            feedback.giver = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted successfully!')
            return redirect('feedback_dashboard')
    else:
        form = FeedbackForm()
    
    context = {
        'project': project,
        'form': form,
    }
    return render(request, 'core/give_feedback.html', context)

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
