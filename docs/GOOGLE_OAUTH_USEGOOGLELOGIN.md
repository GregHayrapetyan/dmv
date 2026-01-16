# Google OAuth with useGoogleLogin Hook

This guide shows how to use the `useGoogleLogin` hook (which provides access tokens) with your backend.

## Backend Changes (Already Completed ✅)

Your backend now accepts **both**:
- `id_token` (from `GoogleLogin` component) - JWT format
- `access_token` (from `useGoogleLogin` hook) - OAuth access token

## Frontend Implementation with useGoogleLogin

### 1. Install Package

```bash
npm install @react-oauth/google
# or
yarn add @react-oauth/google
```

### 2. Wrap Your App

In your main app file (`App.jsx` or `_app.js`):

```jsx
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId="820609526748-sm3ifam2hoi2sgobrdkhiukti4gvu8j1.apps.googleusercontent.com">
      {/* Your routes */}
      <YourRoutes />
    </GoogleOAuthProvider>
  );
}

export default App;
```

### 3. Login Page with useGoogleLogin Hook

```jsx
import { useGoogleLogin } from '@react-oauth/google';
import { useState } from 'react';

function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      setError('');
      
      try {
        console.log('Access token received:', tokenResponse.access_token);
        
        // Send access_token to your backend
        const response = await fetch('http://localhost:8000/api/accounts/google/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_token: tokenResponse.access_token  // ✅ Send access_token
          })
        });

        const data = await response.json();
        console.log('Backend response:', data);
        
        if (data.success) {
          // Store the JWT access token from your backend
          localStorage.setItem('access_token', data.data.access);
          localStorage.setItem('user', JSON.stringify(data.data.user));
          
          // Redirect to dashboard
          window.location.href = '/dashboard';
        } else {
          setError(data.error || 'Login failed');
        }
      } catch (error) {
        console.error('Error during Google login:', error);
        setError('An error occurred during login');
      } finally {
        setLoading(false);
      }
    },
    onError: (error) => {
      console.error('Google Sign-In failed:', error);
      setError('Google Sign-In failed. Please try again.');
    },
    scope: 'email profile',  // Request email and profile scopes
  });

  return (
    <div className="login-container">
      <h1>Login</h1>
      
      {/* Email/Password form */}
      <form onSubmit={handleEmailLogin}>
        <input type="email" placeholder="Email" />
        <input type="password" placeholder="Password" />
        <button type="submit">Login</button>
      </form>

      {/* Custom Google button */}
      <button 
        onClick={handleGoogleLogin}
        disabled={loading}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          padding: '12px 24px',
          border: '1px solid #dadce0',
          borderRadius: '4px',
          background: 'white',
          cursor: loading ? 'not-allowed' : 'pointer',
          width: '100%',
          marginTop: '16px',
          opacity: loading ? 0.6 : 1
        }}
      >
        <img 
          src="https://www.google.com/favicon.ico" 
          alt="Google" 
          width="20" 
          height="20"
        />
        <span>{loading ? 'Signing in...' : 'Continue with Google'}</span>
      </button>

      {error && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}

      <p>
        Don't have an account yet? <a href="/registration">Registration</a>
      </p>
    </div>
  );
}

export default LoginPage;
```

### 4. With Custom Styled Button

```jsx
import { useGoogleLogin } from '@react-oauth/google';
import { useState } from 'react';

function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoading(true);
      
      try {
        const response = await fetch('http://localhost:8000/api/accounts/google/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_token: tokenResponse.access_token
          })
        });

        const data = await response.json();
        
        if (data.success) {
          localStorage.setItem('access_token', data.data.access);
          window.location.href = '/dashboard';
        } else {
          setError(data.error || 'Login failed');
        }
      } catch (error) {
        setError('An error occurred during login');
      } finally {
        setLoading(false);
      }
    },
    onError: () => setError('Google Sign-In failed'),
    scope: 'email profile',
  });

  return (
    <div>
      {/* Your custom button */}
      <button 
        onClick={() => googleLogin()}
        className="google-button"
        disabled={loading}
      >
        <GoogleIcon />
        Continue with Google
      </button>

      {error && <div className="error">{error}</div>}
    </div>
  );
}
```

## How It Works

### Frontend Flow (useGoogleLogin):
1. User clicks your custom button
2. `useGoogleLogin` opens Google OAuth popup
3. User selects account and grants permissions
4. Google returns an **access_token** (e.g., `ya29.A0Aa7pCA...`)
5. Frontend sends `access_token` to your backend

### Backend Flow:
1. Receives `access_token`
2. Makes request to Google's userinfo endpoint: `https://www.googleapis.com/oauth2/v2/userinfo`
3. Gets user profile data (email, name, etc.)
4. Creates or finds user in database
5. Returns your app's JWT tokens

## API Request Format

```javascript
// What your frontend sends
POST http://localhost:8000/api/accounts/google/
Content-Type: application/json

{
  "access_token": "ya29.A0Aa7pCA-LE9MbVlkdEv2edDftBsFlxf64Z2lL2xNK..."
}
```

## API Response Format

```javascript
// Success response
{
  "success": true,
  "message": "Google authentication successful",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // Your app's JWT token
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_email_verified": true
    }
  },
  "error": null
}

// Error response
{
  "success": false,
  "message": "Invalid or expired Google access token.",
  "data": null,
  "error": "INVALID_TOKEN"
}
```

## Comparison: useGoogleLogin vs GoogleLogin

| Feature | useGoogleLogin | GoogleLogin |
|---------|---------------|-------------|
| Token Type | Access Token (`ya29...`) | ID Token (`eyJ...`) |
| Custom Button | ✅ Yes | ❌ No (renders own button) |
| Backend Verification | Calls Google API | Verifies JWT locally |
| Use Case | Custom UI | Standard Google button |

## Troubleshooting

### Error: "Invalid or expired Google access token"

**Cause**: Access token expired or invalid

**Solution**: 
- Access tokens expire quickly (usually 1 hour)
- Make sure you're sending the token immediately after receiving it
- Check network logs to see the actual token being sent

### Error: "Email not provided by Google"

**Cause**: Missing email scope

**Solution**: Add `scope: 'email profile'` to `useGoogleLogin` config

### CORS Errors

**Cause**: Frontend origin not in backend CORS settings

**Solution**: Add your frontend URL to `.env`:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Testing

1. Click the Google button
2. Select a Google account
3. Check browser console for:
   - Access token received
   - Backend response
4. Should redirect to dashboard on success
5. Check backend logs: `tail -f debug.log`

## Security Notes

1. **Access tokens are short-lived** (1 hour typically)
2. **Never store Google access tokens** - only store your app's JWT
3. **Always use HTTPS in production**
4. **Backend validates with Google** - frontend can't fake tokens

## Production Checklist

- [ ] Use production Google OAuth Client ID
- [ ] Set `DEBUG=False` in backend
- [ ] Use HTTPS for all requests
- [ ] Configure proper CORS origins
- [ ] Test token expiration handling
- [ ] Add error tracking/logging
