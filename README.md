# FeedbackLoop

A platform for giving and receiving feedback on projects.

## Email Notifications

FeedbackLoop now includes email notifications for important events:

- When users receive feedback on their projects
- When a user's feedback is liked by a project owner

### Setup Email Notifications

1. Create a `.env` file in the project root with the following variables:
   ```
   MAILERSEND_API_KEY=your-api-key
   MAILERSEND_FROM_EMAIL=your-verified-sender@example.com
   MAILERSEND_REPLY_EMAIL=reply-to@example.com
   SITE_URL=your-site-url (e.g., http://localhost:8000 for development)
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Enable or disable email notifications in settings.py:
   ```python
   SEND_EMAIL_NOTIFICATIONS = True  # Set to False to disable
   ```

### Email Backend

For development, emails are logged to the console. To send real emails in production, update the `EMAIL_BACKEND` setting in settings.py.