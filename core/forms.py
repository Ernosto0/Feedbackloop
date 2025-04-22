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
        fields = ['title', 'url', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
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
    """Form for submitting feedback."""
    class Meta:
        model = Feedback
        fields = ['positives', 'improvements', 'suggestions']
        widgets = {
            'positives': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What aspects of the project are well done?'}),
            'improvements': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What could be improved?'}),
            'suggestions': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Any additional suggestions or ideas?'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    class Meta:
        model = Profile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        } 