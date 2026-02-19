/**
 * AWS Lambda + API Gateway Integration with JWT
 * =============================================
 * 
 * API Endpoints:
 * - POST /admin/login (returns JWT token + refresh token)
 * - POST /admin/refresh (refresh expired token)
 * - POST /customers/register (customer registration)
 * - GET /customers (fetch all customers - requires JWT)
 * - DELETE /customers/{id} (soft delete - requires JWT)
 * 
 * Authentication Flow:
 * 1. User logs in → receives accessToken (1 hour) + refreshToken (7 days)
 * 2. Access token stored in localStorage
 * 3. Token auto-refreshes 5 minutes before expiration
 * 4. Protected endpoints include Authorization header
 * 5. Logout clears all tokens
 */

import { decodeToken, isTokenExpired } from '@/lib/jwt';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';
const TOKEN_KEY = 'adminToken';
const REFRESH_TOKEN_KEY = 'adminRefreshToken';

// ============= Interfaces =============

export interface Customer {
  id: string;
  nicNumber: string;
  fullName: string;
  phoneNumber: string;
  loyaltyNumber: string;
  registeredAt: string;
  isDeleted?: boolean; // For soft delete support
}

export interface RegisterCustomerRequest {
  nicNumber: string;
  fullName: string;
  phoneNumber: string;
}

export interface RegisterCustomerResponse {
  success: boolean;
  loyaltyNumber?: string;
  error?: string;
}

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginResponse {
  success: boolean;
  token?: string; // JWT access token
  refreshToken?: string; // JWT refresh token
  error?: string;
}

// ============= Token Management Functions =============

/**
 * Retrieve JWT access token from localStorage
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Retrieve JWT refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store both access and refresh tokens
 * @param token - JWT access token (1 hour expiration)
 * @param refreshToken - JWT refresh token (7 days expiration)
 */
export function setTokens(token: string, refreshToken?: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Clear all authentication tokens
 * Called on logout or token validation failure
 */
export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Refresh JWT access token using refresh token
 * Best Practice: Proactively refresh before expiration
 * 
 * @returns boolean - true if refresh successful, false otherwise
 */
export async function refreshToken(): Promise<boolean> {
  try {
    const refreshTokenValue = getRefreshToken();
    if (!refreshTokenValue) {
      console.warn('No refresh token available');
      return false;
    }

    // Call Lambda endpoint to refresh token
    const response = await fetch(`${API_BASE_URL}/admin/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refreshToken: refreshTokenValue }),
    });

    if (!response.ok) {
      // Refresh failed - clear tokens and require re-login
      clearTokens();
      return false;
    }

    const data = await response.json();
    // Update tokens with new ones
    setTokens(data.token, data.refreshToken);
    return true;
  } catch (error) {
    console.error('Error refreshing token:', error);
    clearTokens();
    return false;
  }
}

/**
 * Generate authorization header with valid JWT token
 * Automatically refreshes token if expired
 * Best Practice: Always check token freshness before API calls
 * 
 * @returns Authorization header object or empty if no token
 */
async function getAuthHeader(): Promise<Record<string, string>> {
  let token = getToken();

  // Token exists - check if expired
  if (token && isTokenExpired(token)) {
    console.log('Token expired, attempting refresh...');
    const refreshed = await refreshToken();
    if (!refreshed) {
      // Refresh failed - return empty header
      // Component should handle 401 and redirect to login
      return {};
    }
    token = getToken();
  }

  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ============= API Functions =============

/**
 * Admin Login
 * Endpoint: POST /admin/login
 * 
 * Best Practice: Credentials sent via HTTPS, never stored in code
 * Returns both access token (short-lived) and refresh token (long-lived)
 */
export async function adminLogin(
  request: AdminLoginRequest
): Promise<AdminLoginResponse> {
  try {
    // Send login credentials to Lambda
    const response = await fetch(`${API_BASE_URL}/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return {
        success: false,
        error: errorData.error || 'Login failed',
      };
    }

    const data = await response.json();
    
    // Store JWT tokens (access + refresh)
    if (data.token) {
      setTokens(data.token, data.refreshToken);
    }

    return {
      success: true,
      token: data.token,
    };
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
  }
}

/**
 * Register New Customer
 * Endpoint: POST /customers/register
 * 
 * Public endpoint (no JWT required)
 * Validates NIC and phone before submission
 */
export async function registerCustomer(
  request: RegisterCustomerRequest
): Promise<RegisterCustomerResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/customers/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return {
        success: false,
        error: errorData.error || 'Registration failed',
      };
    }

    const data = await response.json();
    return {
      success: true,
      loyaltyNumber: data.loyaltyNumber,
    };
  } catch (error) {
    console.error('Registration error:', error);
    return {
      success: false,
      error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
  }
}

/**
 * Fetch All Customers
 * Endpoint: GET /customers
 * 
 * Protected endpoint - requires valid JWT token
 * Token automatically refreshed if expired
 * Returns array of non-deleted customers
 */
export async function fetchCustomers(): Promise<Customer[]> {
  try {
    // Get fresh authorization header (auto-refreshes if needed)
    const authHeaders = await getAuthHeader();
    
    const response = await fetch(`${API_BASE_URL}/customers`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    // Handle 401 - token invalid/expired and refresh failed
    if (response.status === 401) {
      clearTokens();
      // Component should handle this and redirect to login
      window.location.href = '/admin';
      return [];
    }

    if (!response.ok) {
      throw new Error(`Failed to fetch customers: ${response.statusText}`);
    }

    const data = await response.json();
    // Filter out soft-deleted customers on frontend
    return (data.customers || []).filter((c: Customer) => !c.isDeleted);
  } catch (error) {
    console.error('Error fetching customers:', error);
    return [];
  }
}

/**
 * Soft Delete Customer
 * Endpoint: DELETE /customers/{id}
 * 
 * Protected endpoint - requires valid JWT token
 * Best Practice: Soft delete instead of hard delete
 * Sets isDeleted flag and deletedAt timestamp in DynamoDB
 * Allows recovery if needed
 * 
 * @param id - Customer ID to delete
 */
export async function deleteCustomer(id: string): Promise<boolean> {
  try {
    // Get fresh authorization header
    const authHeaders = await getAuthHeader();
    
    const response = await fetch(`${API_BASE_URL}/customers/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    // Handle 401 - token invalid
    if (response.status === 401) {
      clearTokens();
      window.location.href = '/admin';
      return false;
    }

    return response.ok;
  } catch (error) {
    console.error('Error deleting customer:', error);
    return false;
  }
}

// ============= Validation Functions =============

/**
 * Validate Sri Lankan NIC format
 * Supports both old and new formats
 * 
 * Old format: 9 digits + V/X (e.g., 123456789V)
 * New format: 12 digits (e.g., 199012345678)
 */
export function validateNIC(nic: string): boolean {
  const oldFormat = /^[0-9]{9}[VvXx]$/;
  const newFormat = /^[0-9]{12}$/;
  return oldFormat.test(nic) || newFormat.test(nic);
}

/**
 * Validate Sri Lankan phone number
 * Accepts both local and international formats
 * 
 * Local: 07XXXXXXXX (e.g., 0771234567)
 * International: +947XXXXXXXX (e.g., +94771234567)
 */
export function validatePhoneNumber(phone: string): boolean {
  const localFormat = /^07[0-9]{8}$/;
  const internationalFormat = /^\+947[0-9]{8}$/;
  return localFormat.test(phone) || internationalFormat.test(phone);
}

// ============= Authentication Status Functions =============

/**
 * Check if user is authenticated
 * Best Practice: Verify token exists AND is not expired
 * 
 * @returns boolean - true if valid token present, false otherwise
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) {
    return false;
  }

  // Verify token is not expired (includes 5-minute buffer)
  return !isTokenExpired(token);
}

/**
 * Logout admin user
 * Clears all authentication tokens from localStorage
 * Component should redirect to login page after this
 */
export function adminLogout(): void {
  clearTokens();
  // Redirect to login
  window.location.href = '/admin';
}
