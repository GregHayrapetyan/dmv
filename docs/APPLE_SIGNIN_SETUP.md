# Apple Sign In Integration Setup Guide

This guide explains how to set up and use Apple Sign In authentication in the DMV Test Preparation API.

## Overview

The Apple Sign In integration allows users to sign in using their Apple ID, providing a secure and privacy-focused authentication experience. Apple Sign In is **required** for iOS apps that offer third-party authentication options.

## Features

- ✅ Secure token verification using Apple's public keys
- ✅ Automatic user creation on first login
- ✅ Email verification status from Apple
- ✅ Existing user account linking
- ✅ JWT token generation for API access
- ✅ Privacy-focused (users can hide their email)
- ✅ Comprehensive error handling
- ✅ HttpOnly cookie for refresh tokens

## Prerequisites

1. An Apple Developer Account ($99/year)
2. App ID configured in Apple Developer Portal
3. Service ID for Sign in with Apple
4. Private key (.p8 file) for server-to-server authentication

---

## Step 1: Configure Apple Developer Account

### 1.1 Create an App ID

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list)
2. Click the **+** button to create a new identifier
3. Select **App IDs** and click **Continue**
4. Select **App** and click **Continue**
5. Fill in the details:
   - **Description**: DMV Test Preparation
   - **Bundle ID**: `com.yourdomain.dmvapp` (explicit)
6. Under **Capabilities**, enable **Sign in with Apple**
7. Click **Continue** and then **Register**

### 1.2 Create a Service ID

1. Go to [Identifiers](https://developer.apple.com/account/resources/identifiers/list)
2. Click the **+** button
3. Select **Services IDs** and click **Continue**
4. Fill in the details:
   - **Description**: DMV Test Preparation Web Service
   - **Identifier**: `com.yourdomain.dmvapp.service` (this will be your `APPLE_CLIENT_ID`)
5. Click **Continue** and then **Register**
6. Click on the newly created Service ID
7. Enable **Sign in with Apple**
8. Click **Configure** next to Sign in with Apple
9. Configure Web Authentication:
   - **Primary App ID**: Select the App ID you created earlier
   - **Domains and Subdomains**: Add your domain (e.g., `yourdomain.com`)
   - **Return URLs**: Add your callback URLs:
     - `https://yourdomain.com/callback`
     - `http://localhost:3000/callback` (for development)
10. Click **Save** and then **Continue**
11. Click **Register**

### 1.3 Create a Private Key

1. Go to [Keys](https://developer.apple.com/account/resources/authkeys/list)
2. Click the **+** button
3. Fill in the details:
   - **Key Name**: DMV Sign in with Apple Key
4. Enable **Sign in with Apple**
5. Click **Configure** next to Sign in with Apple
6. Select your **Primary App ID** from the dropdown
7. Click **Save**
8. Click **Continue** and then **Register**
9. **Download** the private key file (`.p8` file) - **You can only download this once!**
10. Save the **Key ID** (you'll need this for `APPLE_KEY_ID`)

### 1.4 Get Your Team ID

1. Go to [Membership](https://developer.apple.com/account/#/membership/)
2. Find your **Team ID** (10-character alphanumeric string)
3. Save this for your `APPLE_TEAM_ID`

---

## Step 2: Configure Backend

### 2.1 Add Private Key File

1. Place your downloaded `.p8` file in the project root directory
2. Rename it if needed (e.g., `AuthKey_7D2CG73MZW.p8`)
3. **Important**: Add `.p8` files to `.gitignore` to keep them secure

### 2.2 Update Environment Variables

Add your Apple credentials to your `.env` file:

```env
# Apple Sign In Configuration
APPLE_CLIENT_ID=com.yourdomain.dmvapp.service
APPLE_TEAM_ID=ABC123DEFG
APPLE_KEY_ID=XYZ789HIJK
APPLE_PRIVATE_KEY_PATH=AuthKey_7D2CG73MZW.p8
```

**Configuration Details:**
- `APPLE_CLIENT_ID`: Your Service ID identifier
- `APPLE_TEAM_ID`: Your Apple Developer Team ID
- `APPLE_KEY_ID`: The Key ID from your private key
- `APPLE_PRIVATE_KEY_PATH`: Path to your `.p8` file (relative to project root)

### 2.3 Verify Dependencies

Ensure these packages are in your `requirements.txt`:

```txt
PyJWT==2.10.1
cryptography==42.0.5
requests==2.31.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2.4 Verify Settings

The Apple configuration is already set up in `settings.py`:

```python
# Apple OAuth
APPLE_CLIENT_ID = config('APPLE_CLIENT_ID', default='')
APPLE_TEAM_ID = config('APPLE_TEAM_ID', default='')
APPLE_KEY_ID = config('APPLE_KEY_ID', default='')
APPLE_PRIVATE_KEY_PATH = config('APPLE_PRIVATE_KEY_PATH', default=str(BASE_DIR / 'AuthKey_7D2CG73MZW.p8'))
```

---

## Step 3: Frontend Integration

### Option 1: React Implementation

#### 3.1 Install Apple Sign In Library

```bash
npm install react-apple-signin-auth
# or
yarn add react-apple-signin-auth
```

#### 3.2 Create Apple Sign In Component

```tsx
// components/AppleSignIn.tsx
import React from 'react';
import AppleSignin from 'react-apple-signin-auth';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/accounts';

interface AppleAuthResponse {
  authorization: {
    id_token: string;
    code: string;
  };
  user?: {
    email: string;
    name?: {
      firstName: string;
      lastName: string;
    };
  };
}

const AppleSignInButton: React.FC = () => {
  const handleAppleSignIn = async (response: AppleAuthResponse) => {
    try {
      console.log('Apple Sign In Response:', response);

      // Prepare data for backend
      const payload = {
        id_token: response.authorization.id_token,
        user_data: response.user || null
      };

      // Send to Django backend
      const backendResponse = await axios.post(
        `${API_BASE_URL}/apple/`,
        payload,
        { withCredentials: true } // Important for httpOnly cookies
      );

      console.log('Backend Response:', backendResponse.data);

      // Extract data from standardized response
      const { access, user } = backendResponse.data.data;
      
      // Store access token
      localStorage.setItem('access_token', access);
      
      // Refresh token is automatically stored in httpOnly cookie by backend
      console.log('User logged in:', user);

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (error: any) {
      console.error('Apple Sign In Error:', error);
      if (error.response) {
        const message = error.response.data.message || 'Unknown error';
        alert(`Login failed: ${message}`);
      } else {
        alert('Network error. Please try again.');
      }
    }
  };

  return (
    <div className="apple-signin-container">
      <AppleSignin
        authOptions={{
          clientId: process.env.REACT_APP_APPLE_CLIENT_ID || 'com.yourdomain.dmvapp.service',
          scope: 'email name',
          redirectURI: window.location.origin + '/callback',
          state: 'state',
          nonce: 'nonce',
          usePopup: true, // Use popup for better UX
        }}
        onSuccess={handleAppleSignIn}
        onError={(error) => {
          console.error('Apple Sign In Error:', error);
          alert('Apple Sign In failed. Please try again.');
        }}
        skipScript={false}
        render={(props) => (
          <button
            {...props}
            className="apple-signin-button"
            style={{
              backgroundColor: '#000',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              width: '100%',
              justifyContent: 'center',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
              <path d="M14.94 5.19A4.38 4.38 0 0 0 13 .05a4.44 4.44 0 0 0-3 1.59 4.12 4.12 0 0 0-1.07 3.17 3.69 3.69 0 0 0 2.26-.56c.1-.06.19-.14.27-.23A4.33 4.33 0 0 0 14.94 5.19ZM13 5.81a5.07 5.07 0 0 0-2.52.67 5.77 5.77 0 0 1-1.92.71 5.77 5.77 0 0 1-1.92-.71 5.07 5.07 0 0 0-2.52-.67A5.19 5.19 0 0 0 0 10.93a10.63 10.63 0 0 0 .58 3.5 7.71 7.71 0 0 0 1.81 3 3.5 3.5 0 0 0 2.55 1.15 4.82 4.82 0 0 0 2.18-.65 4.82 4.82 0 0 1 2.18-.65 4.82 4.82 0 0 1 2.18.65 4.82 4.82 0 0 0 2.18.65 3.5 3.5 0 0 0 2.55-1.15 7.71 7.71 0 0 0 1.81-3A10.63 10.63 0 0 0 18 10.93 5.19 5.19 0 0 0 13 5.81Z"/>
            </svg>
            Sign in with Apple
          </button>
        )}
      />
    </div>
  );
};

export default AppleSignInButton;
```

#### 3.3 Add to Your Login Page

```tsx
// pages/Login.tsx
import AppleSignInButton from '../components/AppleSignIn';
import GoogleSignInButton from '../components/GoogleSignIn';

function LoginPage() {
  return (
    <div className="login-container">
      <h1>Sign In</h1>
      
      {/* Regular email/password form */}
      <form>
        {/* ... your email/password fields ... */}
      </form>
      
      <div className="divider">Or sign in with</div>
      
      {/* Social login buttons */}
      <div className="social-login">
        <AppleSignInButton />
        <GoogleSignInButton />
      </div>
    </div>
  );
}
```

### Option 2: Vanilla JavaScript Implementation

#### 3.1 HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apple Sign In - DMV Test Prep</title>
    
    <!-- Apple Sign In SDK -->
    <script src="https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js"></script>
    
    <style>
        .apple-signin-container {
            width: 250px;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <div class="login-page">
        <h1>Sign In</h1>
        
        <!-- Apple Sign In Button -->
        <div class="apple-signin-container">
            <div id="appleid-signin" 
                 data-color="black" 
                 data-border="true" 
                 data-type="sign in"
                 style="width: 100%; height: 50px;">
            </div>
        </div>
    </div>

    <script src="apple-signin.js"></script>
</body>
</html>
```

#### 3.2 JavaScript Implementation

```javascript
// apple-signin.js
const API_BASE_URL = 'http://localhost:8000/api/accounts';

// Initialize Apple Sign In when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Apple ID authentication
  AppleID.auth.init({
    clientId: 'com.yourdomain.dmvapp.service', // Your Service ID
    scope: 'name email',
    redirectURI: window.location.origin + '/callback',
    state: '[STATE]', // Random string for CSRF protection
    nonce: '[NONCE]', // Random string for replay protection
    usePopup: true, // Use popup instead of redirect
  });

  // Listen for successful authorization
  document.addEventListener('AppleIDSignInOnSuccess', async (event) => {
    try {
      console.log('Apple Sign In Success:', event.detail);

      const { authorization, user } = event.detail;

      // Prepare payload for backend
      const payload = {
        id_token: authorization.id_token,
        user_data: user || null
      };

      // Send to Django backend
      const response = await fetch(`${API_BASE_URL}/apple/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important: Include cookies
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        console.log('Login successful:', data);

        // Store access token
        localStorage.setItem('access_token', data.data.access);
        
        // User data
        console.log('Logged in user:', data.data.user);

        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        console.error('Login failed:', data);
        alert(data.message || 'Login failed. Please try again.');
      }

    } catch (error) {
      console.error('Error during Apple Sign In:', error);
      alert('An error occurred during sign in. Please try again.');
    }
  });

  // Listen for authorization failure
  document.addEventListener('AppleIDSignInOnFailure', (event) => {
    console.error('Apple Sign In Failed:', event.detail);
    alert('Apple Sign In failed. Please try again.');
  });
});
```

### Option 3: Next.js Implementation

#### 3.1 Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/accounts
NEXT_PUBLIC_APPLE_CLIENT_ID=com.yourdomain.dmvapp.service
NEXT_PUBLIC_APPLE_REDIRECT_URI=http://localhost:3000/callback
```

#### 3.2 Apple Sign In Component

```tsx
// components/AppleSignInButton.tsx
'use client';

import { useState, useEffect } from 'react';
import Script from 'next/script';

const AppleSignInButton = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleAppleSignIn = async (event: any) => {
    setIsLoading(true);
    
    try {
      const { authorization, user } = event.detail;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/apple/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Important for cookies
        body: JSON.stringify({
          id_token: authorization.id_token,
          user_data: user || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.data.access);
        window.location.href = '/dashboard';
      } else {
        alert(data.message || 'Login failed');
      }
    } catch (error) {
      console.error('Apple Sign In Error:', error);
      alert('An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleSuccess = (event: any) => handleAppleSignIn(event);
    const handleFailure = (event: any) => {
      console.error('Apple Sign In Failed:', event.detail);
      alert('Apple Sign In failed');
    };

    document.addEventListener('AppleIDSignInOnSuccess', handleSuccess);
    document.addEventListener('AppleIDSignInOnFailure', handleFailure);

    return () => {
      document.removeEventListener('AppleIDSignInOnSuccess', handleSuccess);
      document.removeEventListener('AppleIDSignInOnFailure', handleFailure);
    };
  }, []);

  return (
    <>
      <Script
        src="https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js"
        onLoad={() => {
          (window as any).AppleID.auth.init({
            clientId: process.env.NEXT_PUBLIC_APPLE_CLIENT_ID,
            scope: 'name email',
            redirectURI: process.env.NEXT_PUBLIC_APPLE_REDIRECT_URI,
            usePopup: true,
          });
        }}
      />
      
      <div 
        id="appleid-signin" 
        data-color="black" 
        data-border="true" 
        data-type="sign in"
        className="w-64 h-12"
      />
    </>
  );
};

export default AppleSignInButton;
```

---

## Step 4: Authentication Service (React/Next.js)

Create a centralized authentication service:

```typescript
// services/authService.ts
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || process.env.NEXT_PUBLIC_API_URL;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Always include cookies
});

export const authService = {
  /**
   * Apple Sign In
   */
  async appleLogin(idToken: string, userData: any = null) {
    const response = await api.post('/apple/', {
      id_token: idToken,
      user_data: userData
    });
    return response.data;
  },

  /**
   * Google Sign In
   */
  async googleLogin(idToken: string) {
    const response = await api.post('/google/', {
      id_token: idToken
    });
    return response.data;
  },

  /**
   * Email/Password Login
   */
  async emailLogin(identifier: string, password: string) {
    const response = await api.post('/login/', {
      identifier,
      password
    });
    return response.data;
  },

  /**
   * Refresh Access Token
   */
  async refreshToken() {
    const response = await api.post('/token/refresh/', {});
    return response.data;
  },

  /**
   * Logout
   */
  async logout() {
    const token = localStorage.getItem('access_token');
    const response = await api.post('/logout/', {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    localStorage.removeItem('access_token');
    return response.data;
  },

  /**
   * Get Current User
   */
  async getCurrentUser() {
    const token = localStorage.getItem('access_token');
    const response = await api.get('/me/', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};
```

---

## API Endpoint Documentation

### POST `/api/accounts/apple/`

Authenticate a user with Apple Sign In.

#### Request Headers

```
Content-Type: application/json
```

#### Request Body

```json
{
  "id_token": "eyJraWQiOiJmaDZCczhDIiwiYWxnIjoiUlMyNTYifQ...",
  "user_data": {
    "name": {
      "firstName": "John",
      "lastName": "Doe"
    },
    "email": "john.doe@example.com"
  }
}
```

**Fields:**
- `id_token` (required): Apple ID token JWT
- `user_data` (optional): User information (only provided on first sign-in)

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Apple authentication successful",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_email_verified": true
    }
  }
}
```

**Note:** The refresh token is set as an httpOnly cookie and won't appear in the response body.

#### Error Responses

**400 Bad Request** - Invalid token or email not verified

```json
{
  "success": false,
  "message": "Email not verified by Apple",
  "error": {
    "code": "EMAIL_NOT_VERIFIED",
    "details": null
  }
}
```

**401 Unauthorized** - Invalid or expired token

```json
{
  "success": false,
  "message": "Invalid Apple token",
  "error": {
    "code": "INVALID_TOKEN",
    "details": null
  }
}
```

**503 Service Unavailable** - Apple OAuth not configured

```json
{
  "success": false,
  "message": "Apple authentication is not configured",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "details": null
  }
}
```

---

## Security Considerations

### Backend Security

1. **Token Verification**: The backend verifies tokens using Apple's public keys
2. **Key Rotation**: Public keys are fetched on each request to handle key rotation
3. **Audience Validation**: Token must be issued for your specific Client ID
4. **Expiration Checking**: Expired tokens are rejected
5. **Email Verification**: Only Apple-verified emails are accepted
6. **HTTPS Required**: Always use HTTPS in production

### Frontend Security

1. **Never Expose Private Key**: The `.p8` file must never be accessible to frontend
2. **Secure Token Storage**: 
   - Access token in localStorage (short-lived)
   - Refresh token in httpOnly cookie (more secure)
3. **CORS Configuration**: Properly configure allowed origins
4. **State & Nonce**: Use random values to prevent CSRF and replay attacks

### Privacy Considerations

1. **Hide My Email**: Apple allows users to hide their real email
   - Users get a relay email like `xyz@privaterelay.appleid.com`
   - Emails sent to this address are forwarded to the user
   - Treat it as a normal email address
2. **Name Availability**: User name is only provided on first sign-in
   - Store it when provided
   - Don't expect it on subsequent logins

---

## Testing

### Testing in Development

1. **Use Apple's Test Environment**:
   - Create test Apple IDs at [appleid.apple.com](https://appleid.apple.com)
   - Test with different scenarios (hide email, show email, etc.)

2. **Test the Backend Endpoint**:

```bash
# You'll need a valid id_token from a real Apple Sign In attempt
curl -X POST http://localhost:8000/api/accounts/apple/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_APPLE_ID_TOKEN_HERE",
    "user_data": {
      "name": {
        "firstName": "Test",
        "lastName": "User"
      }
    }
  }'
```

### Manual Testing Checklist

- [ ] First-time sign in (with name data)
- [ ] Subsequent sign in (without name data)
- [ ] Sign in with "Hide My Email" enabled
- [ ] Sign in with existing email account
- [ ] Token expiration handling
- [ ] Invalid token rejection
- [ ] Network error handling
- [ ] Cookie persistence across requests

---

## Troubleshooting

### "Invalid Apple token" Error

**Causes:**
- Token has expired (Apple tokens are short-lived)
- Token was issued for a different Client ID
- Network issues fetching Apple's public keys
- Invalid token format

**Solutions:**
- Ensure `APPLE_CLIENT_ID` matches your Service ID
- Check that the token is fresh (not expired)
- Verify network connectivity to `appleid.apple.com`
- Check server logs for detailed error messages

### "Email not verified by Apple" Error

**Cause:**
- User's Apple account email is not verified

**Solution:**
- Ask user to verify their email with Apple
- This is a security feature and should not be bypassed

### "Apple authentication is not configured" Error

**Cause:**
- Missing configuration in `.env` file

**Solution:**
- Ensure all Apple credentials are set:
  ```env
  APPLE_CLIENT_ID=com.yourdomain.dmvapp.service
  APPLE_TEAM_ID=ABC123DEFG
  APPLE_KEY_ID=XYZ789HIJK
  APPLE_PRIVATE_KEY_PATH=AuthKey_7D2CG73MZW.p8
  ```
- Restart Django server after updating `.env`

### "Failed to fetch Apple public keys" Error

**Cause:**
- Network connection issue
- Apple services are down
- Firewall blocking requests

**Solution:**
- Check internet connectivity
- Verify server can reach `https://appleid.apple.com/auth/keys`
- Check firewall rules

### CORS Errors

**Cause:**
- Frontend origin not in `CORS_ALLOWED_ORIGINS`

**Solution:**
- Add your frontend URL to settings:
  ```python
  CORS_ALLOWED_ORIGINS = [
      "http://localhost:3000",
      "https://yourdomain.com",
  ]
  ```

### Private Relay Email Issues

**Scenario:**
- User signs in with "Hide My Email"
- Gets email like `xyz@privaterelay.appleid.com`

**Solution:**
- Treat it as a normal email
- Emails sent to this address will be forwarded
- User can manage relay settings in Apple ID settings

---

## User Flow Diagrams

### New User Flow (First-time Sign In)

```
1. User clicks "Sign in with Apple"
   ↓
2. Apple authentication popup appears
   ↓
3. User authenticates with Apple ID
   ↓
4. User chooses email preference (show/hide)
   ↓
5. Frontend receives id_token + user data
   ↓
6. Frontend sends data to /api/accounts/apple/
   ↓
7. Backend verifies token with Apple's public keys
   ↓
8. Backend creates new user account
   ↓
9. Backend generates JWT tokens
   ↓
10. Backend sets refresh token cookie
   ↓
11. Frontend receives access token + user data
   ↓
12. User is logged in → Redirect to dashboard
```

### Returning User Flow

```
1. User clicks "Sign in with Apple"
   ↓
2. Apple authentication popup appears
   ↓
3. User authenticates with Apple ID
   ↓
4. Frontend receives id_token (no user data)
   ↓
5. Frontend sends to /api/accounts/apple/
   ↓
6. Backend verifies token
   ↓
7. Backend finds existing user by email
   ↓
8. Backend generates JWT tokens
   ↓
9. Backend sets refresh token cookie
   ↓
10. Frontend receives access token + user data
   ↓
11. User is logged in → Redirect to dashboard
```

---

## Token Refresh Implementation

### Automatic Token Refresh with Axios Interceptor

```typescript
// utils/axiosConfig.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,
});

// Add access token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auto-refresh on 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh token (refresh token is in httpOnly cookie)
        const response = await axios.post(
          `${process.env.REACT_APP_API_URL}/token/refresh/`,
          {},
          { withCredentials: true }
        );

        const { access } = response.data.data;
        localStorage.setItem('access_token', access);
        
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## Production Checklist

### Apple Developer Configuration
- [ ] Production Service ID created and configured
- [ ] Production domains added to Service ID
- [ ] Production redirect URIs configured
- [ ] Private key (.p8) securely stored
- [ ] Key ID and Team ID documented

### Backend Configuration
- [ ] Production `.env` file configured with Apple credentials
- [ ] Private key file secured (not in git)
- [ ] `DEBUG=False` in production
- [ ] HTTPS enabled for all endpoints
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] `CORS_ALLOWED_ORIGINS` limited to production domains
- [ ] Rate limiting enabled
- [ ] Logging configured for production
- [ ] Error monitoring set up (e.g., Sentry)

### Frontend Configuration
- [ ] Production Apple Client ID configured
- [ ] Production API URL configured
- [ ] Production redirect URIs match backend
- [ ] HTTPS enabled
- [ ] Error handling implemented
- [ ] Loading states implemented
- [ ] Token refresh mechanism working
- [ ] Logout functionality tested

### Security
- [ ] All secrets in environment variables
- [ ] HTTPS enforced
- [ ] CORS properly restricted
- [ ] Rate limiting active
- [ ] httpOnly cookies for refresh tokens
- [ ] Token expiration properly handled
- [ ] Input validation on all endpoints

### Testing
- [ ] Test with real Apple ID
- [ ] Test "Hide My Email" feature
- [ ] Test first-time vs returning user
- [ ] Test token expiration
- [ ] Test network errors
- [ ] Test concurrent logins
- [ ] Test logout functionality
- [ ] Load testing performed

---

## Common Integration Patterns

### Combined with Google OAuth

```tsx
// SocialLoginButtons.tsx
import AppleSignInButton from './AppleSignInButton';
import GoogleSignInButton from './GoogleSignInButton';

export default function SocialLoginButtons() {
  return (
    <div className="social-login-container">
      <h3>Or sign in with</h3>
      <div className="button-group">
        <AppleSignInButton />
        <GoogleSignInButton />
      </div>
    </div>
  );
}
```

### Error Handling

```typescript
// utils/errorHandler.ts
export const handleAuthError = (error: any) => {
  if (error.response) {
    const { message, error: errorDetails } = error.response.data;
    
    switch (errorDetails?.code) {
      case 'INVALID_TOKEN':
        return 'Your session has expired. Please sign in again.';
      case 'EMAIL_NOT_VERIFIED':
        return 'Please verify your email with Apple first.';
      case 'SERVICE_UNAVAILABLE':
        return 'Apple Sign In is temporarily unavailable.';
      default:
        return message || 'Authentication failed. Please try again.';
    }
  } else if (error.request) {
    return 'Network error. Please check your connection.';
  } else {
    return 'An unexpected error occurred.';
  }
};
```

---

## Additional Resources

### Official Documentation
- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)
- [Sign in with Apple JS](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_js)
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple)

### Libraries
- [react-apple-signin-auth](https://www.npmjs.com/package/react-apple-signin-auth)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [cryptography Library](https://cryptography.io/)

### Related Documentation
- [Google OAuth Setup Guide](./GOOGLE_OAUTH_SETUP.md)
- [API Response Standard](./API_RESPONSE_STANDARD.md)
- [HttpOnly Cookie Implementation](./HTTPONLY_COOKIE_IMPLEMENTATION.md)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs in `debug.log`
3. Check browser console for frontend errors
4. Verify all environment variables are set
5. Test with Apple's documentation examples
6. Open an issue on the repository

---

## Version History

- **v1.0** (Feb 2026): Initial Apple Sign In implementation
  - Token verification with Apple's public keys
  - User creation and authentication
  - HttpOnly cookie support
  - Comprehensive error handling
