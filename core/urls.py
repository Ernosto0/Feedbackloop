from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('project/submit/', views.submit_project, name='submit_project'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/edit/', views.update_project, name='update_project'),
    path('project/<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('feedback/', views.feedback_dashboard, name='feedback_dashboard'),
    path('feedback/<int:project_id>/give/', views.give_feedback, name='give_feedback'),
    path('feedback/<int:feedback_id>/like/', views.like_feedback, name='like_feedback'),
    path('feedback/<int:feedback_id>/report/', views.report_feedback, name='report_feedback'),
    path('project/<int:project_id>/get-feedback/<int:credits>/', views.get_feedback, name='get_feedback'),
    path('notifications/count/', views.get_notification_count, name='notification_count'),
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notification/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
] 