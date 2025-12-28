# SEMI Ecosystem

A comprehensive learning platform for American Sign Language with admin management capabilities and email verification.

## Features

### User Features
- **User Registration & Login**: Secure user authentication system
- **Email Verification**: Users must verify their email before accessing the platform
- **Admin Approval**: New users require admin approval before they can log in
- **Sign Language Translator**: Interactive ASL translation tool
- **Course Management**: Access to structured ASL courses
- **Progress Tracking**: Monitor learning progress and achievements
- **Quiz System**: Interactive quizzes to test knowledge

### Admin Features
- **Admin Dashboard**: Comprehensive overview of platform statistics
- **User Management**: Approve, reject, and manage user accounts
- **Course Management**: Add, edit, and delete courses
- **Email Notifications**: Automatic email notifications for user actions
- **User Analytics**: Track user engagement and platform usage

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Gmail account for email functionality
- Git (for cloning the repository)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd SEMI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Email Configuration

**Note**: Email verification is currently disabled by default to allow immediate testing. To enable email verification and admin notifications, you need to configure Gmail:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. **Update the configuration** in `app.py`:
   ```python
   EMAIL_USER = 'your-email@gmail.com'
   EMAIL_PASSWORD = 'your-app-password'  # Use the generated app password
   ```
4. **Enable email verification** by changing this line in `app.py`:
   ```python
   ENABLE_EMAIL_VERIFICATION = True  # Change from False to True
   ```

### 4. Admin Account Setup

The system automatically creates an admin account on first run:
- **Email**: `mezmure048@gmail.com` (configurable in `app.py`)
- **Password**: `admin123` (change this in production)
- **Username**: `admin`

**Important**: Change the admin password in production by modifying the `ADMIN_PASSWORD` variable in `app.py`.

### 5. Running the Application

```bash
# Run the Flask application
python app.py

# The application will be available at:
# http://127.0.0.1:5000
```

## Usage

### For Regular Users

1. **Register**: Create a new account with email verification
2. **Verify Email**: Click the verification link sent to your email
3. **Wait for Approval**: Admin will review and approve your account
4. **Start Learning**: Access courses, translator, and other features

### For Admins

1. **Login**: Use admin credentials to access the system
2. **Dashboard**: View platform statistics and recent activity
3. **User Management**: 
   - Review pending user registrations
   - Approve or reject user accounts
   - Monitor user status and verification
4. **Course Management**:
   - Add new courses with detailed information
   - Edit existing course content
   - Remove outdated courses

## File Structure

```
SEMI/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── data/                 # Data storage (JSON files)
│   ├── users.json       # User accounts and data
│   ├── courses.json     # Course information
│   ├── translations.json # User translation history
│   ├── favorites.json   # User favorite translations
│   └── progress.json    # User learning progress
├── static/               # Static assets
│   ├── style.css        # Main stylesheet
│   ├── script.js        # JavaScript functionality
│   └── sign/            # Sign language images/GIFs
└── templates/            # HTML templates
    ├── admin/           # Admin panel templates
    │   ├── dashboard.html
    │   ├── users.html
    │   └── courses.html
    ├── dashboard.html   # User dashboard
    ├── home.html        # Landing page
    ├── login.html       # Login form
    ├── register.html    # Registration form
    └── ...              # Other templates
```

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Flask-Login for secure user sessions
- **Admin Protection**: Decorator-based admin access control
- **Email Verification**: Prevents fake email registrations
- **Admin Approval**: Manual review of new user accounts

## Email Templates

The system sends several types of emails:

1. **Verification Email**: Sent to new users for email verification
2. **Admin Notifications**: Sent to admin for new registrations and verifications
3. **Approval Emails**: Sent to users when their account is approved
4. **Rejection Emails**: Sent to users when their account is rejected

## Customization

### Adding New Admin Features

1. Create new routes in `app.py` with the `@admin_required` decorator
2. Add corresponding templates in `templates/admin/`
3. Update the admin navigation in admin templates

### Modifying Email Templates

Edit the email functions in `app.py`:
- `send_verification_email()`: User verification emails
- `send_admin_notification()`: Admin notification emails

### Adding New User Roles

1. Extend the User class in `app.py`
2. Add role-based decorators similar to `@admin_required`
3. Update templates to show role-specific content

## Troubleshooting

### Email Issues
- Ensure Gmail 2FA is enabled
- Use App Password, not regular password
- Check firewall/antivirus settings
- Verify Gmail account permissions

### Registration/Login Issues
- **"Registration failed"**: This usually means email verification failed. Check if `ENABLE_EMAIL_VERIFICATION = False` in `app.py` for immediate testing
- **"Invalid username or password"**: Ensure the user was created successfully during registration
- **"Account pending approval"**: Only appears when email verification is enabled and admin approval is required

### Admin Access Issues
- Check if admin user exists in `data/users.json`
- Verify admin email matches `ADMIN_EMAIL` in `app.py`
- Ensure admin user has `is_admin: true` and `status: approved`

### Database Issues
- Check file permissions for `data/` directory
- Verify JSON files are valid
- Restart application after manual data changes

## Production Deployment

Before deploying to production:

1. **Change Secret Key**: Update `SECRET_KEY` in `app.py`
2. **Change Admin Password**: Update `ADMIN_PASSWORD`
3. **Use Production WSGI Server**: Use Gunicorn or uWSGI instead of Flask dev server
4. **Secure Email**: Use environment variables for email credentials
5. **HTTPS**: Enable SSL/TLS for secure communication
6. **Database**: Consider using a proper database instead of JSON files

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Flask and Flask-Login documentation
- Ensure all dependencies are correctly installed
- Verify email configuration settings

## License

This project is for educational purposes. Please ensure compliance with any third-party licenses for sign language content and images.
