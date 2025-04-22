from django.contrib import admin
from .models import Profile, Project, Feedback, Tag

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits')
    search_fields = ('user__username', 'user__email')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'tags')
    search_fields = ('title', 'description', 'owner__username')
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('project', 'giver', 'created_at', 'is_liked', 'is_reported')
    list_filter = ('is_liked', 'is_reported', 'created_at')
    search_fields = ('project__title', 'giver__username', 'positives', 'improvements', 'suggestions')
    date_hierarchy = 'created_at'
