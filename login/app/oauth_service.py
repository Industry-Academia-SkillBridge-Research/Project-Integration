"""
OAuth service layer using Authlib for Google OAuth 2.0
"""
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.config import settings

# Initialize OAuth configuration
config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
})

# Create OAuth registry
oauth = OAuth(config)

# Register Google OAuth provider with extended timeout
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        # Request access_type=offline for refresh tokens if needed
        # 'access_type': 'offline',
        # 'prompt': 'consent',
    },
    # Increase timeout for metadata loading
    httpx_client_kwargs={
        "timeout": 30.0,  # 30 seconds timeout instead of default 5
        "follow_redirects": True,
    }
)


def get_oauth_client():
    """
    Get the configured OAuth client instance.

    Returns:
        OAuth client for Google authentication

    Usage:
        oauth_client = get_oauth_client()
        redirect_uri = request.url_for('auth_callback')
        return await oauth_client.google.authorize_redirect(request, redirect_uri)
    """
    return oauth.google


# You can easily add more OAuth providers here:
# Example for GitHub:
"""
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)
"""

# Example for Microsoft:
"""
oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
"""
