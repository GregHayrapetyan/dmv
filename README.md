# DMV Test Preparation API

A comprehensive Django REST API for a DMV (Department of Motor Vehicles) test preparation application. This backend provides authentication, user onboarding, and a complete learning/testing system.

## Features

### 🔐 Authentication & Accounts
- Email/Phone registration with OTP verification
- JWT-based authentication
- Password reset via email OTP
- Google OAuth integration
- Rate limiting on OTP endpoints

### 👤 User Onboarding
- User profile management
- State selection
- Vehicle type selection (Car, Motorcycle, CDL)
- Knowledge level assessment

### 📚 Learning System
- Lesson categories and lessons
- Video and theory-based content
- Comprehensive test system
- Multiple-choice questions with images
- Automatic scoring and feedback
- Demo tests for practice

## Tech Stack

- **Framework**: Django 5.2.7
- **API**: Django REST Framework 3.16.1
- **Authentication**: JWT (SimpleJWT)
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Image Processing**: Pillow
- **CORS**: django-cors-headers

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   cd dmv
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure your settings:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Email Configuration (for OTP)
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   
   # Google OAuth (optional)
   GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000`

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Main Endpoints

#### Authentication (`/api/accounts/`)
- `POST /register/` - Register new user
- `POST /login/` - Login with email/phone
- `POST /token/refresh/` - Refresh JWT token
- `POST /email/confirm/` - Confirm email with OTP
- `POST /password/forgot/` - Request password reset
- `POST /password/reset/` - Reset password with OTP
- `POST /google/` - Google OAuth login

#### Onboarding (`/api/onboarding/`)
- `GET /states/` - List all states
- `GET /profile/` - Get user profile
- `PUT /profile/` - Update user profile

#### Learning (`/api/learning/`)
- `GET /categories/` - List lesson categories
- `GET /lessons/` - List lessons (filter by `?category=<id>`)
- `GET /lessons/<slug>/` - Get lesson details
- `GET /test-categories/` - List test categories
- `GET /tests/` - List tests (filter by `?category=<id>&demo=true`)
- `GET /tests/<id>/` - Get test with questions
- `POST /tests/<id>/submit/` - Submit test answers

## Management Commands

### Cleanup Expired OTPs
Remove expired and old used OTP codes:
```bash
python manage.py cleanup_expired_otps --days 7
```

## Project Structure

```
dmv/
├── accounts/           # User authentication & management
│   ├── models.py      # User, EmailOTP models
│   ├── serializers.py # API serializers
│   ├── views.py       # API views
│   ├── urls.py        # URL routing
│   └── throttling.py  # Rate limiting
├── onboarding/        # User onboarding & profiles
│   ├── models.py      # Profile, State models
│   ├── signals.py     # Auto-create profiles
│   └── views.py       # Profile management
├── learning/          # Learning & testing system
│   ├── models.py      # Lesson, Test, Question models
│   ├── serializers.py # API serializers
│   ├── views.py       # Learning API views
│   └── admin.py       # Enhanced admin interface
├── dmv/               # Project settings
│   ├── settings.py    # Configuration
│   └── urls.py        # Main URL routing
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
└── README.md         # This file
```

## Development

### Admin Interface
Access the Django admin at `http://localhost:8000/admin/`

The admin interface includes:
- User management with email verification status
- OTP code monitoring
- Lesson and test content management
- Inline editing for questions and answers

### Adding Content

1. **Create Lesson Categories** via admin
2. **Create Lessons** and assign to categories
3. **Create Test Categories** linked to lesson categories
4. **Create Tests** for each lesson
5. **Add Questions** with multiple answer options
6. Mark correct answers and add explanations

### Rate Limiting

OTP endpoints are rate-limited to prevent abuse:
- Anonymous users: 5 requests/hour for OTP endpoints
- Authenticated users: 1000 requests/hour general
- Anonymous users: 100 requests/hour general

## Security Considerations

### For Production:

1. **Environment Variables**
   - Never commit `.env` file
   - Use strong `SECRET_KEY`
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS` properly

2. **Database**
   - Switch to PostgreSQL
   - Use connection pooling
   - Regular backups

3. **Email**
   - Use proper SMTP service
   - Configure SPF/DKIM records

4. **HTTPS**
   - Use SSL certificates
   - Configure secure cookies

5. **CORS**
   - Restrict `CORS_ALLOWED_ORIGINS` to your frontend domain

## API Usage Examples

### Register User
```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "password": "SecurePass123"
  }'
```

### Get Lessons
```bash
curl -X GET http://localhost:8000/api/learning/lessons/ \
  -H "Authorization: Bearer <your-access-token>"
```

### Submit Test
```bash
curl -X POST http://localhost:8000/api/learning/tests/1/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "1": 3,
      "2": 7,
      "3": 11
    }
  }'
```

## Logging

Logs are written to:
- Console (stdout)
- `debug.log` file in project root

Log levels can be configured in `settings.py`

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.
