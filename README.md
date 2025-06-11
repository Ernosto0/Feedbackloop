# Feedbackloop

**A credit-based platform where developers exchange meaningful feedback on each other's projects.** Launch faster, improve better — one feedback at a time.

**Give feedback to get feedback**

🧑‍💻 **Solo project** – Designed, developed, and deployed entirely by me.

🌐 **Live Site**: [https://loopfeedback.dev](https://loopfeedback.dev)

🔗 **Live demo:**

## 🌟 Features

### Project Management
- Submit and showcase your projects
- Upload multiple project images
- Tag projects for better categorization
- Toggle project visibility (active/inactive)
- Delete projects when needed

### Feedback System
- Credit-based feedback exchange
- Give feedback to earn credits
- Request specific types of feedback
- Set feedback priority levels
- Customize feedback prompts
- React to received feedback with emojis
- Report inappropriate feedback

### User Profile
- Personalized user profiles
- Track given and received feedback
- Monitor feedback credits
- View earned badges
- Manage notifications

### Gamification
- Credit system for fair exchange
- Badge system for achievements
- Notification system for engagement
- Upvote/downvote feedback

## 📁 Project Structure

```
feedbackloop/
├── core/                   # Main application directory
│   ├── migrations/        # Database migrations
│   ├── management/        # Custom management commands
│   ├── views.py          # Handles HTTP requests and responses
│   ├── models.py         # Database models
│   ├── forms.py          # Form definitions
│   ├── urls.py           # URL routing
│   ├── utils.py          # Utility functions
│   ├── admin.py          # Admin interface
│   ├── analytics.py      # Analytics tracking
│   └── emailer.py        # Email handling
│
├── templates/             # HTML templates
│   ├── core/             # Core app templates
│   ├── registration/     # Auth-related templates
│   └── base.html         # Base template
│
├── static/               # Static files (Images)
│   └── images/
│
│
├── docs/                 # Documentation
│
├── feedbackloop/         # Project configuration
│   ├── settings.py      # Project settings
│   ├── urls.py          # Main URL routing
│   └── wsgi.py          # WSGI configuration
│
├── manage.py            # Django management script
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

## 💻 Technical Highlights

### Backend Development
- **Django Framework**: Built a robust web application using Django's MVT architecture
- **Database Design**: Implemented complex data models with Django ORM
  - User authentication and profile management
  - Project and feedback management system
  - Notification system
  - Badge and credit system
- **API Development**: Used RESTful endpoints for dynamic interactions
- **Authentication & Authorization**: Implemented secure user authentication and role-based access control, Google Auth

### Frontend Development
- **Frontend**: Tailwind CSS
- **Interactive UI**: Implemented AJAX for seamless user interactions
- **Responsive Design**: Ensured mobile-friendly user interface

### Security Features
- **Input Validation**: Robust form validation and sanitization
- **Access Control**: Role-based permission system
- **Security Middleware**: Custom middleware for enhanced security

### System Design
- **Credit System**: Designed and implemented a fair exchange system for feedback
- **Notification System**: Real-time notification system for user engagement via e-mails (Mailersend)
- **File Management**: Handled file uploads and media storage (Cloudinary)


### Best Practices
- **Code Organization**: Modular code structure with clear separation of concerns
- **Documentation**: Comprehensive inline documentation and API documentation
- **Testing**: Unit tests for critical components
- **Version Control**: Organized Git workflow
- **Error Handling**: Robust error handling and user feedback

### Additional Skills
- **Analytics Integration**: Custom analytics tracking
- **Email System**: Automated email notifications
- **Performance Optimization**: Database query optimization
- **Deployment**: Production deployment configuration

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- Django
- PostgreSQL (recommended for production)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Ernosto0/Feedbackloop
cd feedbackloop
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add:
```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url

Optional: Media & Email 
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

MAILERSEND_API_KEY=your_mailersend_key

```
5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 💡 Usage

1. **Sign Up/Login**: Create an account or login to access the platform
2. **Submit Project**: Share your project with title, description, and images
3. **Request Feedback**: Use credits to request feedback on your projects
4. **Give Feedback**: Review others' projects to earn credits
5. **Manage Profile**: Track your activity and manage notifications

## 🔒 Security Features

- User authentication and authorization
- Protected views with login requirements
- Secure feedback reporting system
- Ban system for policy violations

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Cinar Aksoy - ernosto20.03@gmail.com

https://www.linkedin.com/in/cinar-aksoy-5023a1240/


## 🙏 Acknowledgments

- Django Framework
- Tailwind CSS for responsive UI
- All contributors who participate in this project