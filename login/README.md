# OAuth 2.0 Authentication System with FastAPI

A production-ready OAuth 2.0 authentication system built with FastAPI, Google OAuth, JWT tokens, and MySQL database. This backend API allows users to log in with their Google account and automatically registers new users on first login.

## Features

- **Google OAuth 2.0 Authentication** using Authlib
- **Automatic User Registration** on first login
- **JWT Token Generation** for secure API access
- **MySQL Database** integration with SQLAlchemy ORM
- **CORS Support** for frontend integration
- **RESTful API** with comprehensive documentation
- **Extensible Design** - easily add more OAuth providers (GitHub, Microsoft, etc.)

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Authlib** - OAuth 2.0 client library
- **SQLAlchemy** - Database ORM
- **PyMySQL** - MySQL connector
- **Python-JOSE** - JWT token handling
- **MySQL** - Database for user storage

## Project Structure

```
login/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy User model
│   ├── auth_utils.py        # JWT token utilities
│   ├── oauth_service.py     # OAuth configuration
│   └── routes/
│       ├── __init__.py
│       └── auth.py          # Authentication endpoints
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- MySQL server running locally or remotely
- Google Cloud Console account for OAuth credentials

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Set Up MySQL Database

```sql
-- Create database
CREATE DATABASE oauth_users;

-- Create user (optional)
CREATE USER 'oauth_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON oauth_users.* TO 'oauth_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
   - Add authorized JavaScript origins: `http://localhost:8000`
   - Add authorized redirect URIs: `http://localhost:8000/auth/google/callback`
6. Copy your **Client ID** and **Client Secret**

### 5. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
```

Update `.env` with your values:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/oauth_users

# JWT Configuration (generate a secure random string for production)
SECRET_KEY=your-super-secret-key-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Application URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Environment
ENVIRONMENT=development
```

### 6. Run the Application

```bash
# Option 1: Using Python directly
python -m app.main

# Option 2: Using Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication Flow

#### 1. Initiate Login
```
GET /auth/login/google
```
Redirects user to Google OAuth consent screen.

#### 2. OAuth Callback (automatic)
```
GET /auth/google/callback
```
Receives authorization code from Google, creates/updates user, and redirects to frontend with JWT token.

#### 3. Get Current User
```
GET /auth/me
Headers:
  Authorization: Bearer <jwt_token>
```
Returns authenticated user information.

#### 4. Logout
```
POST /auth/logout
```
Logout endpoint (frontend should clear token).

#### 5. Health Check
```
GET /auth/health
GET /health
```
Check API health status.

## Frontend Integration (React Example)

### Login Flow

```jsx
// Login button click
const handleLogin = () => {
  window.location.href = 'http://localhost:8000/auth/login/google';
};

// Callback page - extract token from URL
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  const error = urlParams.get('error');

  if (token) {
    // Store token
    localStorage.setItem('access_token', token);
    // Redirect to dashboard
    navigate('/dashboard');
  } else if (error) {
    console.error('Authentication failed:', error);
  }
}, []);
```

### Authenticated Requests

```jsx
// Fetch user data
const fetchUser = async () => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.ok) {
    const userData = await response.json();
    console.log(userData);
  }
};
```

### Logout

```jsx
const handleLogout = () => {
  // Clear token
  localStorage.removeItem('access_token');

  // Optional: call logout endpoint
  fetch('http://localhost:8000/auth/logout', { method: 'POST' });

  // Redirect to login
  navigate('/login');
};
```

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(512),
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_provider_user (provider, provider_user_id)
);
```

## Security Best Practices

1. **Never commit `.env` file** - contains sensitive credentials
2. **Use HTTPS in production** - set `https_only=True` in SessionMiddleware
3. **Generate strong SECRET_KEY** - use `openssl rand -hex 32`
4. **Set secure CORS origins** - only allow trusted frontend URLs
5. **Use environment-specific configs** - separate dev/staging/production
6. **Rotate secrets regularly** - change JWT secret keys periodically
7. **Implement rate limiting** - protect against brute force attacks
8. **Enable database backups** - protect user data

## Adding More OAuth Providers

Uncomment and configure in `app/oauth_service.py`:

### GitHub
```python
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)
```

### Microsoft
```python
oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test authentication (will redirect to Google)
curl -L http://localhost:8000/auth/login/google

# Test with JWT token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/auth/me
```

## Common Issues & Solutions

### Issue: "Could not connect to database"
- Ensure MySQL server is running
- Check DATABASE_URL in `.env`
- Verify database exists and credentials are correct

### Issue: "OAuth callback fails"
- Verify Google OAuth redirect URI matches exactly: `http://localhost:8000/auth/google/callback`
- Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in `.env`
- Ensure OAuth consent screen is configured

### Issue: "Token validation fails"
- Check SECRET_KEY is set and consistent
- Verify token hasn't expired (default 60 minutes)
- Ensure Authorization header format: `Bearer <token>`

### Issue: "CORS errors in frontend"
- Add your frontend URL to CORS_ORIGINS in `app/config.py`
- Check FRONTEND_URL in `.env` matches your React app URL

## Production Deployment

1. **Use environment variables** - never hardcode secrets
2. **Enable HTTPS** - use SSL/TLS certificates
3. **Use production ASGI server** - Gunicorn with Uvicorn workers
4. **Set up reverse proxy** - Nginx or Apache
5. **Configure firewall** - restrict database access
6. **Enable logging** - monitor errors and access
7. **Use managed database** - AWS RDS, Google Cloud SQL, etc.

### Production Run Command
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## License

MIT License - feel free to use for personal or commercial projects.

## Support

For issues or questions:
1. Check [FastAPI Documentation](https://fastapi.tiangolo.com/)
2. Check [Authlib Documentation](https://docs.authlib.org/)
3. Review Google OAuth 2.0 setup guide

## Contributing

Contributions welcome! Please follow standard Git workflow:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
