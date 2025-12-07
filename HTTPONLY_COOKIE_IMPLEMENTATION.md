# httpOnly Cookie Implementation for Refresh Tokens

## Overview
The refresh token is now stored in an httpOnly cookie instead of being returned in the response body. This improves security by preventing JavaScript access to the refresh token, protecting against XSS attacks.

## Changes Made

### 1. **LoginView** (`accounts/views.py`)
- Modified to set refresh token as httpOnly cookie
- Only returns `access` token in response body
- Cookie settings:
  - `httponly=True` - Prevents JavaScript access
  - `secure=not DEBUG` - HTTPS only in production
  - `samesite='Lax'` - CSRF protection
  - `max_age=7*24*60*60` - 7 days (matches JWT settings)
  - `path='/api/accounts/token/refresh/'` - Only sent to refresh endpoint

### 2. **GoogleLoginView** (`accounts/views.py`)
- Updated to also set refresh token as httpOnly cookie
- Same cookie settings as LoginView

### 3. **CookieTokenRefreshView** (`accounts/views.py`)
- New custom view that reads refresh token from cookies
- Automatically extracts token from `refresh_token` cookie
- Supports token rotation (updates cookie with new refresh token)
- No request body needed - token is sent automatically via cookie

### 4. **LogoutView** (`accounts/views.py`)
- New view to clear the refresh token cookie
- Requires authentication
- Deletes the `refresh_token` cookie

### 5. **URLs** (`accounts/urls.py`)
- Updated to use `CookieTokenRefreshView` instead of default `TokenRefreshView`
- Added logout endpoint: `/api/accounts/logout/`

### 6. **Settings** (`dmv/settings.py`)
- Added cookie security settings:
  - `SESSION_COOKIE_SECURE = not DEBUG`
  - `CSRF_COOKIE_SECURE = not DEBUG`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`
  - `CSRF_COOKIE_SAMESITE = 'Lax'`

## API Endpoints

### Login
**POST** `/api/accounts/login/`
- **Request Body**: `{ "identifier": "email@example.com", "password": "password123" }`
- **Response**: Returns access token and user info (refresh token set in cookie)
```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_email_verified": true
    }
  },
  "message": "Login successful"
}
```

### Refresh Token
**POST** `/api/accounts/token/refresh/`
- **Request Body**: None (token sent automatically via cookie)
- **Response**: Returns new access token
```json
{
  "status": "success",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Token refreshed successfully"
}
```

### Logout
**POST** `/api/accounts/logout/`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: Clears refresh token cookie
```json
{
  "status": "success",
  "data": null,
  "message": "Logged out successfully"
}
```

## Frontend Integration

### Required Changes

1. **Enable Credentials in HTTP Requests**
   ```javascript
   // Using fetch
   fetch('http://localhost:8000/api/accounts/login/', {
     method: 'POST',
     credentials: 'include',  // Important!
     headers: {
       'Content-Type': 'application/json',
     },
     body: JSON.stringify({ identifier: 'user@example.com', password: 'password123' })
   });

   // Using axios
   axios.post('http://localhost:8000/api/accounts/login/', data, {
     withCredentials: true  // Important!
   });
   ```

2. **Store Access Token in Memory (Not localStorage)**
   ```javascript
   // Store in memory (more secure)
   let accessToken = null;

   async function login(identifier, password) {
     const response = await fetch('/api/accounts/login/', {
       method: 'POST',
       credentials: 'include',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ identifier, password })
     });
     const data = await response.json();
     accessToken = data.data.access;  // Store in memory
     return data;
   }
   ```

3. **Refresh Token Automatically**
   ```javascript
   async function refreshAccessToken() {
     const response = await fetch('/api/accounts/token/refresh/', {
       method: 'POST',
       credentials: 'include'  // Cookie sent automatically
     });
     const data = await response.json();
     accessToken = data.data.access;
     return accessToken;
   }
   ```

4. **Logout**
   ```javascript
   async function logout() {
     await fetch('/api/accounts/logout/', {
       method: 'POST',
       credentials: 'include',
       headers: {
         'Authorization': `Bearer ${accessToken}`
       }
     });
     accessToken = null;  // Clear from memory
   }
   ```

### Axios Interceptor Example
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true
});

let accessToken = null;

// Request interceptor to add access token
api.interceptors.request.use(
  config => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const { data } = await api.post('/accounts/token/refresh/');
        accessToken = data.data.access;
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        accessToken = null;
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export { api, accessToken };
```

## Security Benefits

1. **XSS Protection**: Refresh token cannot be accessed by JavaScript
2. **CSRF Protection**: `SameSite=Lax` prevents cross-site request forgery
3. **HTTPS Only in Production**: `secure=True` ensures cookies only sent over HTTPS
4. **Limited Scope**: Cookie only sent to `/api/accounts/token/refresh/` endpoint
5. **Short-lived Access Tokens**: Access token in memory is lost on page refresh (user stays logged in via refresh token)

## Testing

Test the implementation:

```bash
# Login
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "user@example.com", "password": "password123"}' \
  -c cookies.txt

# Refresh token (using saved cookies)
curl -X POST http://localhost:8000/api/accounts/token/refresh/ \
  -b cookies.txt

# Logout
curl -X POST http://localhost:8000/api/accounts/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -b cookies.txt
```

## Production Considerations

1. **HTTPS Required**: In production, set `DEBUG=False` to enable `secure=True` on cookies
2. **CORS Configuration**: Ensure `CORS_ALLOWED_ORIGINS` includes your frontend domain
3. **Cookie Domain**: For subdomains, you may want to set `domain` parameter in `set_cookie()`
4. **SameSite Policy**: Consider using `'Strict'` instead of `'Lax'` for maximum security (may affect some OAuth flows)

## Environment Variables

Make sure these are set in production:
```env
DEBUG=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days
```
