# FeedbackLoop Prelaunch Guide

This guide explains how to manage FeedbackLoop's prelaunch mode, including the waitlist system, disabling regular pages, and launching the site.

## Understanding Prelaunch Mode

FeedbackLoop has two modes:

1. **Development Mode** (`DEVELOPMENT=True`): Shows the full application with all pages and features.
2. **Prelaunch Mode** (`DEVELOPMENT=False`): Shows only the waitlist landing page and a few essential pages (about, terms, etc.).

## Toggling Between Modes

You can switch between development mode and prelaunch mode using the provided management command:

```bash
# Toggle between modes (switches to the opposite of current mode)
python manage.py toggle_prelaunch

# Force prelaunch mode on (DEVELOPMENT=False)
python manage.py toggle_prelaunch --on

# Force development mode on (DEVELOPMENT=True)
python manage.py toggle_prelaunch --off
```

After toggling the mode, you need to restart the Django server for the changes to take effect.

## Waitlist System

### How It Works

When in prelaunch mode:
- Visitors can only access the waitlist landing page, about page, privacy policy, and terms of service.
- All other pages redirect to the waitlist landing page.
- The waitlist form collects email addresses and optional names.
- Admin users can still access the admin panel at `/admin/`.

### Managing Waitlist Entries

You can view and manage waitlist entries through the Django admin panel:

1. Go to `/admin/` and log in with admin credentials.
2. Navigate to "Core" > "Waitlist entries".
3. Here you can see all the subscribers, search by email/name, and export the list if needed.

You can also use the command line to check waitlist statistics:

```bash
# Check the current waitlist count and stats
python manage.py waitlist_count

# List all waitlist entries with email addresses and signup dates
python manage.py waitlist_count --list
```

## Launching the Site

When you're ready to launch FeedbackLoop and notify all waitlist subscribers:

1. Ensure your email settings are configured correctly in your `.env` file:
   ```
   MAILERSEND_API_KEY=your_api_key
   MAILERSEND_FROM_EMAIL=your_sender_email
   MAILERSEND_REPLY_EMAIL=your_reply_email
   SEND_EMAIL_NOTIFICATIONS=True
   ```

2. Run the notify waitlist command:
   ```bash
   python manage.py notify_waitlist
   ```
   This will send a launch notification email to all waitlist subscribers.

3. Switch to development mode:
   ```bash
   python manage.py toggle_prelaunch --off
   ```

4. Restart your server:
   ```bash
   python manage.py runserver
   ```

## Important Notes

- **Email Template**: The email template for waitlist notifications is defined in `core/emailer.py`. You can customize it as needed.
- **Home Page Redirect**: When in prelaunch mode, the home URL (`/`) redirects to the waitlist page.
- **Allowed Pages**: The middleware allows access to the waitlist page, about page, admin pages, and static/media files.
- **Admin Access**: Admin users can still access the admin panel in prelaunch mode by navigating directly to `/admin/`.
- **Waitlist Bonus**: The launch notification email mentions a 3-credit bonus for waitlist members. Be sure to implement this when users from the waitlist sign up.

## Implementing the Waitlist Bonus

When users from the waitlist register, you'll want to give them the promised 3 bonus credits. This can be implemented by:

1. Checking if the email used for registration matches one in the waitlist.
2. If it matches, adding 2 additional credits to the default 1 credit.

Example implementation (to be added to the signup view):

```python
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            
            # Check if email is in waitlist
            from core.models import WaitlistEntry
            waitlist_match = WaitlistEntry.objects.filter(email=email).exists()
            
            if waitlist_match:
                # Add 2 bonus credits (default is already 1)
                user.profile.credits += 2
                user.profile.save()
                messages.success(
                    request, 
                    'Thanks for joining from our waitlist! We\'ve added 3 credits to your account to get started.'
                )
            else:
                messages.success(request, 'Account created successfully! You now have 1 credit to start.')
                
            # Log in the user
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})
```

This implementation should be added when you're ready to launch the site.