from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Project, Feedback, Profile, Tag, PRICING_CHOICES, ProjectImage, WaitlistEntry

class SignUpForm(UserCreationForm):
    """Form for user registration."""
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


FEEDBACK_CHOICES = [
    ('ui', 'UI / Design'),
    ('ux', 'UX / Usability'),
    ('bug', 'Bug Finding'),
    ('copy', 'Copywriting / Clarity'),
    ('ideas', 'New Feature Ideas'),
    ('overall', 'Overall Impression'),
]

class ProjectForm(forms.ModelForm):
    """Form for submitting a project."""

    # Custom tag field with autocomplete
    tags_input = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas (e.g., portfolio, landing page, app)"
    )

    # Tech stack used
    tech_stack = forms.CharField(
        required=False,
        label="Tech Stack Used",
        help_text="E.g., React, Tailwind, Django, PostgreSQL",
        widget=forms.TextInput(attrs={'class': 'w-full', 'placeholder': 'React, Tailwind, Django'})
    )

    # Pricing plan
    pricing_plan = forms.ChoiceField(
        choices=PRICING_CHOICES,
        required=True,
        label="Pricing Model",
        widget=forms.Select(attrs={'class': 'w-full'})
    )

    # Guest access info if project is paid-only
    guest_access_info = forms.CharField(
        required=False,
        label="Guest Access (if paid only)",
        help_text="Provide a demo login, trial link, or discount code for reviewers if your project is not free.",
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full',
            'placeholder': 'e.g., username: demo@example.com, password: test123'
        })
    )

    class Meta:
        model = Project
        fields = ['title', 'url', 'description', 'photo']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full', 'placeholder': 'My Awesome Project'}),
            'url': forms.URLInput(attrs={'class': 'w-full', 'placeholder': 'https://myproject.com'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full',
                'placeholder': 'Describe your project in detail. What is it about? What technologies did you use?'
            }),
        }
        labels = {
            'title': 'Project Name',
            'url': 'Project Link',
            'description': 'Project Description',
            'photo': 'Project Screenshot/Image',
        }
        help_texts = {
            'photo': 'Upload a screenshot or representative image of your project (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
            
            

    def clean(self):
        cleaned_data = super().clean()
        pricing_plan = cleaned_data.get('pricing_plan')
        guest_access_info = cleaned_data.get('guest_access_info')

        if pricing_plan == 'paid' and not guest_access_info:
            self.add_error(
                'guest_access_info',
                'Since your project is paid-only, please provide a demo link, guest account, or discount code.'
            )

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Ensure feedback_type_wanted is properly handled
        feedback_type = self.cleaned_data.get('feedback_type_wanted', [])
        # Store as a list, not as a string (prevents issues with JSONField)
        instance.feedback_type_wanted = list(feedback_type) if feedback_type else []
        
        instance.tech_stack = self.cleaned_data.get('tech_stack', '')
        instance.pricing_plan = self.cleaned_data.get('pricing_plan', 'free')
        instance.guest_access_info = self.cleaned_data.get('guest_access_info', '')

        if commit:
            instance.save()

            # Process tags
            instance.tags.clear()
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [tag.strip().lower() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    instance.tags.add(tag)

        return instance


class FeedbackForm(forms.ModelForm):
    positives = forms.CharField(
        label="What's Good",
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'rows': 4,
            'placeholder': 'What aspects of the project do you like? What works well?'
        }),
        help_text="Highlight positive aspects of the project"
    )
    
    improvements = forms.CharField(
        label="What Can Be Improved",
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'rows': 4,
            'placeholder': 'What aspects could be improved? Be specific and constructive.'
        }),
        help_text="Suggest areas for improvement"
    )
    
    suggestions = forms.CharField(
        label="Additional Suggestions",
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'rows': 4,
            'placeholder': 'Any other suggestions, ideas, or resources that might help?'
        }),
        required=True,
        help_text="Additional suggestions or resources"
    )
    
    class Meta:
        model = Feedback
        fields = ['positives', 'improvements', 'suggestions']

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'hidden', 'id': 'profile-picture-input'}))
    
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
        }

class UserUpdateForm(forms.ModelForm):
    """Form for updating user information."""
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'}),
        } 

# Create an inline formset for project images
ProjectImageFormSet = inlineformset_factory(
    Project,
    ProjectImage,
    fields=('image', 'caption', 'order'),
    extra=1,
    can_delete=True
) 

class WaitlistForm(forms.ModelForm):
    """Form for waitlist signup."""
    email = forms.EmailField(
        max_length=254, 
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50',
            'placeholder': 'Enter your email address'
        })
    )
    name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50',
            'placeholder': 'Enter your name (optional)'
        })
    )
    
    class Meta:
        model = WaitlistEntry
        fields = ['email', 'name'] 