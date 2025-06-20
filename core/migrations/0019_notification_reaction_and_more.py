# Generated by Django 5.2 on 2025-05-01 20:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_feedbackreaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='reaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.feedbackreaction'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('feedback_received', 'Feedback Received'), ('feedback_liked', 'Feedback Liked'), ('feedback_helpful', 'Feedback Marked as Helpful'), ('feedback_thanks', 'Feedback Thanked'), ('feedback_considering', 'Feedback Being Considered'), ('report_approved', 'Report Approved'), ('report_dismissed', 'Report Dismissed'), ('feedback_reported', 'Feedback Reported'), ('user_warning', 'User Warning'), ('badge_earned', 'Badge Earned')], max_length=20),
        ),
    ]
