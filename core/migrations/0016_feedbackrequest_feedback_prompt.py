# Generated by Django 5.2 on 2025-05-01 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_project_view_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackrequest',
            name='feedback_prompt',
            field=models.TextField(blank=True, help_text='A message from the project owner to guide feedback givers', null=True),
        ),
    ]
