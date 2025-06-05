"""
Email notification system for FeedbackLoop using MailerSend API.
"""
import os
from mailersend import emails
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email(recipient_name, recipient_email, subject, html_content, text_content=None):
    print("Sending email to:", recipient_email)
    """
    Send an email using MailerSend API.
    
    Args:
        recipient_name (str): Name of the recipient
        recipient_email (str): Email of the recipient
        subject (str): Email subject
        html_content (str): HTML content of the email
        text_content (str, optional): Plain text content of the email
    
    Returns:
        dict: Response from MailerSend API
    """
    # Initialize MailerSend
    api_key = os.getenv('MAILERSEND_API_KEY')
    if not api_key:
        print("WARNING: No MailerSend API key found in environment variables")
        return None
        
    mailer = emails.NewEmail(api_key)
    
    # Define an empty dict to populate with mail values
    mail_body = {}
    
    # Set sender details - make sure to use the full email address with the domain
    from_email = os.getenv('MAILERSEND_FROM_EMAIL')
    if not from_email:
        print("WARNING: No sender email found, using default domain")
        from_email = 'noreply@loopfeedback.dev'
        
    mail_from = {
        "name": "FeedbackLoop",
        "email": from_email,
    }
    
    # Set recipient details
    recipients = [
        {
            "name": recipient_name,
            "email": recipient_email,
        }
    ]
    
    # Set reply-to details
    reply_email = os.getenv('MAILERSEND_REPLY_EMAIL')
    if not reply_email:
        print("WARNING: No reply-to email found, using default domain")
        reply_email = 'support@trial-69oxl5e2dzzl785k.mlsender.net'
        
    reply_to = {
        "name": "FeedbackLoop Support",
        "email": reply_email,
    }
    
    # Log email details for debugging
    print(f"Sending email from: {mail_from['email']}")
    print(f"To: {recipient_email}")
    print(f"Subject: {subject}")
    
    # Set email content
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_html_content(html_content, mail_body)
    
    if text_content:
        mailer.set_plaintext_content(text_content, mail_body)
    else:
        # If no plain text content is provided, use a simple version
        mailer.set_plaintext_content(f"{subject}\n\nPlease view this email in an HTML-compatible email client.", mail_body)
    
    mailer.set_reply_to(reply_to, mail_body)
    
    # Debug the mail body content before sending
    print("From email:", mail_from)
    print("Reply to:", reply_to)
    
    # Send the email
    try:
        response = mailer.send(mail_body)
        print(f"Email sent response: {response}")
        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return None

def send_feedback_received_email(recipient_user, feedback):
    print("Sending feedback received email for user:", recipient_user.username, recipient_user.email)
    """
    Send email notification when new feedback is received.
    
    Args:
        recipient_user: User object of the recipient
        feedback: Feedback object
    """
    project = feedback.project
    subject = f"New feedback on your project: {project.title}"
    
    html_content = f"""
    <h2>Hi {recipient_user.username},</h2>
    <p>You've received new feedback on your project <strong>{project.title}</strong> from {feedback.giver.username}.</p>
    <p>Here's a preview of the feedback:</p>
    <blockquote style="border-left: 3px solid #ccc; padding-left: 10px;">
        <p><strong>What's Good:</strong> {feedback.positives[:100]}{'...' if len(feedback.positives) > 100 else ''}</p>
        <p><strong>What Can Be Improved:</strong> {feedback.improvements[:100]}{'...' if len(feedback.improvements) > 100 else ''}</p>
    </blockquote>
    <p><a href="{settings.SITE_URL}/project/{project.id}/feedback/{feedback.id}/">Click here</a> to view the full feedback.</p>
    <p>Thank you for using FeedbackLoop!</p>
    """
    
    return send_email(
        recipient_name=recipient_user.username,
        recipient_email=recipient_user.email,
        subject=subject,
        html_content=html_content
    )

def send_feedback_liked_email(recipient_user, feedback):
    """
    Send email notification when feedback is liked.
    
    Args:
        recipient_user: User object of the recipient
        feedback: Feedback object
    """
    project = feedback.project
    subject = f"Your feedback was liked: {project.title}"
    
    html_content = f"""
    <h2>Hi {recipient_user.username},</h2>
    <p>The owner of <strong>{project.title}</strong> liked your feedback! You have been awarded 1 credit.</p>
    <p>Here's a summary of your feedback:</p>
    <blockquote style="border-left: 3px solid #ccc; padding-left: 10px;">
        <p><strong>What's Good:</strong> {feedback.positives[:100]}{'...' if len(feedback.positives) > 100 else ''}</p>
        <p><strong>What Can Be Improved:</strong> {feedback.improvements[:100]}{'...' if len(feedback.improvements) > 100 else ''}</p>
    </blockquote>
    <p><a href="{settings.SITE_URL}/project/{project.id}/feedback/{feedback.id}/">Click here</a> to view your feedback.</p>
    <p>Thank you for contributing to the FeedbackLoop community!</p>
    """
    
    return send_email(
        recipient_name=recipient_user.username,
        recipient_email=recipient_user.email,
        subject=subject,
        html_content=html_content
    )

def send_launch_notification_email(waitlist_entry):
    """
    Send launch notification email to waitlist subscribers.
    
    Args:
        waitlist_entry: WaitlistEntry object
    """
    recipient_name = waitlist_entry.name if waitlist_entry.name else "there"
    subject = "FeedbackLoop has launched! 🚀"
    
    html_content = f"""
    <h2>Hello {recipient_name},</h2>
    <p>We're excited to announce that <strong>FeedbackLoop</strong> has officially launched!</p>
    <p>Thank you for joining our waitlist. As an early supporter, you now have access to our platform where you can:</p>
    <ul>
        <li>Submit your projects for quality feedback</li>
        <li>Give feedback to others and earn credits</li>
        <li>Connect with fellow creators</li>
        <li>Improve your work through structured, actionable insights</li>
    </ul>
    <p><a href="{settings.SITE_URL}/signup/" style="background-color: #4f46e5; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">Create Your Account Now</a></p>
    <p>As a thank you for your early interest, we're giving each waitlist member <strong>3 bonus credits</strong> to get started!</p>
    <p>We can't wait to see your projects on FeedbackLoop!</p>
    <p>Warm regards,<br>The FeedbackLoop Team</p>
    """
    
    return send_email(
        recipient_name=recipient_name,
        recipient_email=waitlist_entry.email,
        subject=subject,
        html_content=html_content
    ) 