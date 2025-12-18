# OTP API Implementation - Complete Guide

## 🎯 Overview

This document describes the complete OTP (One-Time Password) implementation for email verification and password reset flows.

---

## ✅ Security Fixes Applied

### 1. **Removed OTP from Password Reset Response**
- **Before**: Password reset API returned OTP code in response (SECURITY VULNERABILITY)
- **After**: OTP code is only sent via email (SECURE)

---

## 🔄 New Unified API Flow

### **Endpoint: `/api/accounts/verify-otp/`**

This single endpoint handles both:
- ✅ Email verification (after registration)
- ✅ Password reset verification (after forgot password)

---

## 📋 API Endpoints

### 1. **Registration & Email Verification Flow**

#### Step 1: Register User
```http
POST /api/accounts/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123",
  "repeat_password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "Registration successful. Please check your email for verification code."
}
```

#### Step 2: Verify Email with OTP
```http
POST /api/accounts/verify-otp/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "purpose": "verify_email"
}
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "Email verified successfully"
}
```

---

### 2. **Password Reset Flow**

#### Step 1: Request Password Reset
```http
POST /api/accounts/password/forgot/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "If this email exists, a reset code has been sent."
}
```

#### Step 2: Verify Reset Code
```http
POST /api/accounts/verify-otp/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "654321",
  "purpose": "reset_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "Code verified successfully. You can now reset your password."
}
```

#### Step 3: Reset Password
```http
POST /api/accounts/password/reset/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "654321",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "Password updated successfully"
}
```

---

## 🔧 Debug Endpoint (Development Only)

### **Endpoint: `/api/accounts/debug/get-otp/`**

**⚠️ Only works when `DEBUG=True` in settings**

This endpoint allows you to retrieve OTP codes for testing without checking email.

```http
POST /api/accounts/debug/get-otp/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "email": "user@example.com",
    "verify_email_otp": "123456",
    "reset_password_otp": "654321"
  },
  "message": "OTP codes retrieved (DEBUG MODE ONLY)"
}
```

**Production Behavior:**
```json
{
  "success": false,
  "error_code": "PERMISSION_DENIED",
  "message": "This endpoint is only available in DEBUG mode"
}
```

---

## 🎨 Frontend Implementation Examples

### React/JavaScript Example

```javascript
// Unified OTP verification function
async function verifyOTP(email, code, purpose) {
  const response = await fetch('/api/accounts/verify-otp/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      code,
      purpose
    })
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.message);
  }
  
  return data;
}

// Usage for email verification
try {
  await verifyOTP('user@example.com', '123456', 'verify_email');
  console.log('Email verified!');
} catch (error) {
  console.error('Verification failed:', error.message);
}

// Usage for password reset
try {
  await verifyOTP('user@example.com', '654321', 'reset_password');
  console.log('Code verified! Now you can reset password.');
} catch (error) {
  console.error('Verification failed:', error.message);
}
```

### Development Mode - Auto-fill OTP

```javascript
// In development, automatically get and fill OTP
async function registerAndAutoVerify(email, password) {
  // Step 1: Register
  await fetch('/api/accounts/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      first_name: 'Test',
      last_name: 'User',
      password,
      repeat_password: password
    })
  });
  
  // Step 2: Get OTP (only works in DEBUG mode)
  if (process.env.NODE_ENV === 'development') {
    const otpResponse = await fetch('/api/accounts/debug/get-otp/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    const otpData = await otpResponse.json();
    
    if (otpData.success && otpData.data.verify_email_otp) {
      // Auto-fill the OTP input
      document.getElementById('otp-input').value = otpData.data.verify_email_otp;
      
      // Or auto-verify
      await verifyOTP(email, otpData.data.verify_email_otp, 'verify_email');
    }
  }
}
```

---

## 📊 Database Schema

### EmailOTP Model

```python
class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)  # 6-digit code
    purpose = models.CharField(
        max_length=20,
        choices=[
            ("verify_email", "Verify Email"),
            ("reset_password", "Reset Password")
        ]
    )
    expires_at = models.DateTimeField()  # 10 minutes from creation
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🔒 Security Features

### ✅ Implemented Security Measures

1. **No OTP in API Responses**
   - OTP codes are never returned in API responses
   - Codes are only sent via email

2. **Code Expiration**
   - All OTP codes expire after 10 minutes
   - Expired codes are automatically rejected

3. **Single Use Codes**
   - Each code can only be used once
   - After verification, code is marked as used

4. **Debug Endpoint Protection**
   - Debug OTP retrieval only works when `DEBUG=True`
   - Returns 403 Forbidden in production
   - All access attempts are logged

5. **Email Enumeration Protection**
   - Generic messages don't reveal if email exists
   - "If this email exists..." messaging

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "testpass123",
    "repeat_password": "testpass123"
  }'

# 2. Get OTP (DEBUG mode only)
curl -X POST http://localhost:8000/api/accounts/debug/get-otp/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 3. Verify email
curl -X POST http://localhost:8000/api/accounts/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456",
    "purpose": "verify_email"
  }'
```

---

## 📝 Error Responses

### Invalid or Expired Code
```json
{
  "success": false,
  "message": "OTP verification failed",
  "details": {
    "non_field_errors": ["Invalid or expired code"]
  }
}
```

### User Not Found
```json
{
  "success": false,
  "message": "OTP verification failed",
  "details": {
    "non_field_errors": ["Invalid email or code"]
  }
}
```

### Debug Endpoint in Production
```json
{
  "success": false,
  "error_code": "PERMISSION_DENIED",
  "message": "This endpoint is only available in DEBUG mode"
}
```

---

## 🔄 Migration from Old Endpoints

### Legacy Endpoint (Still Works)
```http
POST /api/accounts/email/confirm/
{
  "email": "user@example.com",
  "code": "123456"
}
```

### New Unified Endpoint (Recommended)
```http
POST /api/accounts/verify-otp/
{
  "email": "user@example.com",
  "code": "123456",
  "purpose": "verify_email"
}
```

**Note**: The old `/email/confirm/` endpoint is marked as deprecated but still functional for backward compatibility.

---

## 📚 Summary

### What Was Implemented

1. ✅ **Fixed security vulnerability** - Removed OTP from password reset response
2. ✅ **Unified OTP verification** - Single endpoint for all OTP verifications
3. ✅ **Debug endpoint** - Get OTP codes in development mode
4. ✅ **Backward compatibility** - Old endpoints still work
5. ✅ **Comprehensive documentation** - This guide

### Files Modified

- `/home/greg/dmv/accounts/serializers.py` - Added `GetOTPSerializer` and `VerifyOTPSerializer`
- `/home/greg/dmv/accounts/views.py` - Added `GetOTPView` and `VerifyOTPView`
- `/home/greg/dmv/accounts/urls.py` - Added new endpoints

### New Endpoints

- `POST /api/accounts/verify-otp/` - Unified OTP verification
- `POST /api/accounts/debug/get-otp/` - Debug-only OTP retrieval

---

## 🎉 Benefits

1. **Single confirmation UI** - Use the same screen for both registration and password reset
2. **Secure** - OTP codes never exposed in API responses
3. **Developer-friendly** - Debug endpoint for easy testing
4. **Production-ready** - Debug features automatically disabled in production
5. **Flexible** - Clear purpose field makes intent explicit
6. **Backward compatible** - Existing integrations continue to work

---

**Last Updated**: December 18, 2025
