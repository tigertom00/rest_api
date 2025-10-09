# Mobile Authentication Guide for Expo App

This guide covers the mobile-optimized authentication system for the memo app's Expo frontend.

## Overview

The backend now supports mobile-first authentication with:
- **JWT tokens** (30 min access, 30 day refresh)
- **Device management** (track sessions, push notifications)
- **Thumbnail generation** (faster image loading)
- **Single-call login** (auth + device registration combined)

## Authentication Endpoints

### 1. Mobile Login (Recommended)
**Endpoint**: `POST /auth/mobile/login/`

Combines authentication and device registration in one call.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "device_type": "ios",                    // Required: "ios", "android", "web"
  "device_name": "iPhone 15",              // Optional but recommended
  "device_id": "unique-device-identifier", // Optional but recommended
  "push_token": "ExponentPushToken[...]",  // Optional - for push notifications
  "os_version": "17.2",                    // Optional
  "app_version": "1.0.0"                   // Optional
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1Qi...",
  "refresh": "eyJ0eXAiOiJKV1Qi...",
  "lifetime": 1800,
  "device_id": "uuid-of-device",
  "user": {
    "id": 1,
    "username": "user",
    "display_name": "User Name",
    "email": "user@example.com",
    "phone": "+1234567890",
    "profile_picture": "/media/profile_image/..."
  }
}
```

### 2. Token Refresh
**Endpoint**: `POST /auth/token/refresh/`

```json
{
  "refresh": "your-refresh-token"
}
```

**Response:**
```json
{
  "access": "new-access-token",
  "refresh": "new-refresh-token"  // Token rotation enabled
}
```

### 3. Logout
**Endpoint**: `POST /auth/token/blacklist/`

```json
{
  "refresh_token": "your-refresh-token"
}
```

## Device Management

### List User's Devices
**Endpoint**: `GET /api/devices/`

Returns all devices for the authenticated user.

### Update Device (e.g., Push Token)
**Endpoint**: `PATCH /api/devices/{device_id}/`

```json
{
  "push_token": "new-push-token"
}
```

### Revoke Device Access
**Endpoint**: `POST /api/devices/{device_id}/revoke/`

### Revoke All Other Devices
**Endpoint**: `POST /api/devices/revoke-all-others/`

```json
{
  "current_device_id": "uuid-of-current-device"
}
```

## Expo Implementation Example

### Initial Setup

```javascript
import * as SecureStore from 'expo-secure-store';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const API_BASE_URL = 'https://your-api.com';
```

### Login Function

```javascript
export const loginUser = async (email, password, expoPushToken) => {
  try {
    const deviceId = await getDeviceId(); // Store/retrieve consistent ID

    const response = await fetch(`${API_BASE_URL}/auth/mobile/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        device_type: Platform.OS,
        device_name: Device.deviceName || `${Platform.OS} Device`,
        device_id: deviceId,
        push_token: expoPushToken,
        os_version: Device.osVersion,
        app_version: Constants.expoConfig?.version || '1.0.0',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Login failed');
    }

    const data = await response.json();

    // Store tokens securely
    await SecureStore.setItemAsync('access_token', data.access);
    await SecureStore.setItemAsync('refresh_token', data.refresh);
    await SecureStore.setItemAsync('device_id', data.device_id);

    // Schedule token refresh (data.lifetime is in seconds)
    scheduleTokenRefresh(data.lifetime);

    return data.user;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};
```

### Auto Token Refresh

```javascript
let refreshTimer;

export const scheduleTokenRefresh = (lifetime) => {
  // Refresh 2 minutes before expiry
  const refreshTime = (lifetime - 120) * 1000;

  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(async () => {
    try {
      await refreshAccessToken();
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Handle logout or re-authentication
    }
  }, refreshTime);
};

export const refreshAccessToken = async () => {
  const refreshToken = await SecureStore.getItemAsync('refresh_token');

  const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!response.ok) throw new Error('Token refresh failed');

  const data = await response.json();

  await SecureStore.setItemAsync('access_token', data.access);
  await SecureStore.setItemAsync('refresh_token', data.refresh);

  scheduleTokenRefresh(1800); // 30 minutes

  return data.access;
};
```

### Authenticated API Calls

```javascript
export const apiCall = async (endpoint, options = {}) => {
  let accessToken = await SecureStore.getItemAsync('access_token');

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  });

  // Handle token expiration
  if (response.status === 401) {
    try {
      accessToken = await refreshAccessToken();

      // Retry request with new token
      return await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      // Refresh failed, logout user
      throw new Error('Session expired');
    }
  }

  return response;
};
```

## Memo App Endpoints

All memo endpoints require authentication:

- `GET /api/memo/jobber/` - List jobs
- `POST /api/memo/jobber/` - Create job
- `GET /api/memo/jobber/{id}/` - Get job details
- `PATCH /api/memo/jobber/{id}/` - Update job
- `GET /api/memo/jobb-images/` - List images (includes `thumbnail` field)
- `POST /api/memo/jobb-images/` - Upload image (thumbnail auto-generated)
- `GET /api/memo/jobber-tasks/` - List tasks
- `POST /api/memo/jobber-tasks/` - Create task

## Image Optimization

Images now include automatic thumbnail generation:

```javascript
// Thumbnail is automatically generated server-side
const image = {
  id: 1,
  image: "https://api.com/media/jobb_images/photo.jpg",
  thumbnail: "https://api.com/media/jobb_images/thumbnails/thumb_photo.jpg",
  created_at: "2025-10-09T..."
};

// Use thumbnail for list views, full image for detail view
<Image source={{ uri: image.thumbnail }} />
```

## Important Notes

### CORS
**Mobile apps don't need CORS configuration** - React Native makes native HTTP requests, not browser requests. CORS is already configured for web frontends only.

### Token Expiration
- Access tokens expire in **30 minutes**
- Refresh tokens expire in **30 days**
- Implement automatic token refresh to avoid interruptions

### Device ID
- Use a consistent device identifier (not just Device.id, which can change)
- Consider using a combination approach or storing a UUID on first launch
- Device ID enables device-specific logout and session management

### Security
- Always use `SecureStore` for tokens (not AsyncStorage)
- Consider implementing biometric authentication (FaceID/TouchID)
- Implement certificate pinning for production
- Handle token refresh failures gracefully with re-authentication

### Push Notifications
- Store Expo push token during login
- Update token when it changes: `PATCH /api/devices/{device_id}/`
- Backend ready for Expo Push Notifications integration

## Testing

Test the authentication flow:

```bash
# Login
curl -X POST http://localhost:8000/auth/mobile/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "device_type": "ios",
    "device_name": "Test Device"
  }'

# Use access token
curl -X GET http://localhost:8000/api/memo/jobber/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh token
curl -X POST http://localhost:8000/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## Support

For questions or issues, contact the backend team or check the main API documentation at `/schema/swagger-ui/`.
