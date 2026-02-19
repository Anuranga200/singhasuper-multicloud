/**
 * JWT Utility Functions
 * =====================
 * Handles token encoding/decoding and validation on the frontend
 * Comments added to key sections for maintainability
 */

interface JWTPayload {
  email: string;
  role: 'admin' | 'user';
  iat: number; // issued at
  exp: number; // expiration time
  userId?: string;
}

/**
 * Decode and validate JWT token
 * NOTE: Frontend decoding for display purposes only
 * SECURITY: Token verification happens on Lambda backend
 */
export function decodeToken(token: string): JWTPayload | null {
  try {
    // Extract payload from JWT (structure: header.payload.signature)
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.warn('Invalid token format');
      return null;
    }

    // Decode payload using base64 (handle URL-safe base64)
    const decoded = JSON.parse(
      atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    );

    return decoded;
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
}

/**
 * Check if token is expired with 5-minute buffer
 * Buffer ensures automatic refresh before actual expiration
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) {
      console.warn('No expiration found in token');
      return true;
    }

    // Convert exp (seconds) to milliseconds
    const expirationTime = decoded.exp * 1000;
    const currentTime = Date.now();

    // Add 5-minute buffer for proactive refresh
    const bufferTime = 5 * 60 * 1000;
    const isExpired = currentTime > (expirationTime - bufferTime);

    return isExpired;
  } catch {
    return true;
  }
}

/**
 * Get token expiration time in seconds
 */
export function getTokenExpiration(token: string): number | null {
  const decoded = decodeToken(token);
  return decoded?.exp || null;
}

/**
 * Extract user info from token payload
 */
export function getUserFromToken(token: string): { email: string; role: string; userId?: string } | null {
  const decoded = decodeToken(token);
  if (!decoded) {
    return null;
  }

  return {
    email: decoded.email,
    role: decoded.role,
    userId: decoded.userId,
  };
}