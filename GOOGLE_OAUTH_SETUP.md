# Google OAuth Integration Setup Guide

This guide explains how to set up and use Google OAuth authentication in the DMV Test Preparation API.

## Overview

The Google OAuth integration allows users to sign in using their Google accounts, providing a seamless authentication experience without requiring password management.

## Features

- ✅ Secure token verification using Google's official library
- ✅ Automatic user creation on first login
- ✅ Email verification status from Google
- ✅ Existing user account linking
- ✅ JWT token generation for API access
- ✅ Comprehensive error handling

## Prerequisites

1. A Google Cloud Platform account
2. A project in Google Cloud Console
3. OAuth 2.0 credentials configured

## Step 1: Create Google OAuth Credentials

### 1.1 Go to Google Cloud Console

Visit [Google Cloud Console](https://console.cloud.google.com/)

### 1.2 Create or Select a Project

- Click on the project dropdown at the top
- Create a new project or select an existing one

### 1.3 Enable Google+ API (Optional but Recommended)

- Go to **APIs & Services** > **Library**
- Search for "Google+ API" or "People API"
- Click **Enable**

### 1.4 Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (for public apps) or **Internal** (for organization)
3. Fill in the required information:
   - **App name**: DMV Test Preparation
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Add scopes:
   - `email`
   - `profile`
   - `openid`
5. Save and continue

### 1.5 Create OAuth 2.0 Client ID

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Configure:
   - **Name**: DMV Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:3000` (development)
     - `https://yourdomain.com` (production)
   - **Authorized redirect URIs**:
     - `http://localhost:3000` (development)
     - `https://yourdomain.com` (production)
5. Click **Create**
6. Copy the **Client ID** (you'll need this for your `.env` file)

## Step 2: Configure Backend

### 2.1 Update Environment Variables

Add your Google OAuth Client ID to your `.env` file:

```env
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
```

### 2.2 Verify Dependencies

Ensure `google-auth` is in your `requirements.txt`:

```
google-auth==2.42.1
```

If not installed, run:

```bash
pip install google-auth
```

## Step 3: Frontend Integration

### 3.1 Install Google Sign-In Library

For React/Next.js:

```bash
npm install @react-oauth/google
# or
yarn add @react-oauth/google
```

### 3.2 Wrap Your App with GoogleOAuthProvider

```jsx
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      {/* Your app components */}
    </GoogleOAuthProvider>
  );
}
```

### 3.3 Implement Google Sign-In Button

```jsx
import { GoogleLogin } from '@react-oauth/google';

function LoginPage() {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/accounts/google/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id_token: credentialResponse.credential
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        
        // Store user data
        console.log('User:', data.user);
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        console.error('Login failed:', data.detail);
      }
    } catch (error) {
      console.error('Error during Google login:', error);
    }
  };

  const handleGoogleError = () => {
    console.error('Google Sign-In failed');
  };

  return (
    <div>
      <h1>Sign In</h1>
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        useOneTap
      />
    </div>
  );
}
```

## API Endpoint

### POST `/api/accounts/google/`

Authenticate a user with Google OAuth.

**Request Body:**

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjI3..."
}
```

**Success Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_email_verified": true
  }
}
```

**Error Responses:**

- **400 Bad Request**: Email not provided or not verified by Google
- **401 Unauthorized**: Invalid or expired token
- **503 Service Unavailable**: Google OAuth not configured

## Security Considerations

### Backend Security

1. **Token Verification**: The backend verifies the token directly with Google's servers
2. **Email Verification**: Only Google-verified emails are accepted
3. **Client ID Validation**: Token must be issued for your specific Client ID
4. **HTTPS Required**: Always use HTTPS in production

### Frontend Security

1. **Never expose Client Secret**: Only use Client ID in frontend
2. **Secure Token Storage**: Store JWT tokens securely (httpOnly cookies recommended)
3. **Token Refresh**: Implement automatic token refresh
4. **CORS Configuration**: Properly configure CORS origins

## Testing

### Test with cURL

```bash
# First, get a valid id_token from Google Sign-In in your browser
# Then test the endpoint:

curl -X POST http://localhost:8000/api/accounts/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_ID_TOKEN_HERE"
  }'
```

### Manual Testing Steps

1. Implement the frontend integration
2. Click the Google Sign-In button
3. Select a Google account
4. Verify you receive JWT tokens
5. Check the Django admin to see the created user
6. Verify `is_email_verified` is set to `True`

## Troubleshooting

### "Invalid Google token" Error

**Causes:**
- Token has expired (tokens are short-lived, ~1 hour)
- Token was issued for a different Client ID
- Network issues during verification

**Solution:**
- Ensure frontend uses the correct Client ID
- Implement proper error handling and retry logic
- Check server logs for detailed error messages

### "Email not verified by Google" Error

**Cause:**
- User's Google account email is not verified

**Solution:**
- Ask user to verify their email with Google
- This is a security feature and should not be bypassed

### "Google authentication is not configured" Error

**Cause:**
- `GOOGLE_OAUTH_CLIENT_ID` not set in `.env`

**Solution:**
- Add your Client ID to `.env` file
- Restart the Django server

### CORS Errors

**Cause:**
- Frontend origin not in `CORS_ALLOWED_ORIGINS`

**Solution:**
- Add your frontend URL to `.env`:
  ```env
  CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
  ```

## User Flow

### New User (First-time Google Sign-In)

1. User clicks "Sign in with Google"
2. Google authentication popup appears
3. User selects Google account
4. Frontend receives `id_token`
5. Frontend sends `id_token` to backend
6. Backend verifies token with Google
7. Backend creates new user account
8. Backend generates JWT tokens
9. Frontend receives tokens and user data
10. User is logged in and redirected

### Existing User (Returning Google Sign-In)

1. User clicks "Sign in with Google"
2. Google authentication popup appears
3. User selects Google account
4. Frontend receives `id_token`
5. Frontend sends `id_token` to backend
6. Backend verifies token with Google
7. Backend finds existing user by email
8. Backend updates email verification status if needed
9. Backend generates JWT tokens
10. Frontend receives tokens and user data
11. User is logged in and redirected

### Existing User (Email/Password → Google Sign-In)

If a user registered with email/password and later signs in with Google using the same email:

1. Backend finds existing user by email
2. Backend updates `is_email_verified` to `True`
3. User can now use both authentication methods

## Production Checklist

- [ ] Use production Google OAuth Client ID
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use HTTPS for all requests
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set secure `CORS_ALLOWED_ORIGINS`
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Test error scenarios
- [ ] Implement token refresh mechanism
- [ ] Add analytics tracking

## Additional Resources

- [Google Identity Documentation](https://developers.google.com/identity)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [@react-oauth/google Documentation](https://www.npmjs.com/package/@react-oauth/google)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs in `debug.log`
3. Check browser console for frontend errors
4. Open an issue on the repository
