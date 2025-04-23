from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Project, Feedback, Profile, Tag

class SignUpForm(UserCreationForm):
    """Form for user registration."""
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
class ProjectForm(forms.ModelForm):
    """Form for submitting a project."""
    # Custom tag field with autocomplete
    tags_input = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas (e.g., portfolio,landing page,app)"
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
            # Pre-populate tags input for editing
            self.fields['tags_input'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Process tags
            self.instance.tags.clear()
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [tag.strip().lower() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    self.instance.tags.add(tag)
        
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
            'placeholder': 'Any other suggestions, ideas, or resources that might help? (Optional)'
        }),
        required=False,
        help_text="Optional additional suggestions or resources"
    )
    
    class Meta:
        model = Feedback
        fields = ['positives', 'improvements', 'suggestions']

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        } 