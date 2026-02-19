# QA Strategy & Testing Guide - Singha Loyalty System

## 🎯 QA Assessment Overview

**Project:** Singha Loyalty System (Server-Based Architecture)
**QA Engineer:** Senior QA Lead
**Date:** January 31, 2026
**Status:** ⚠️ **NO TESTS CURRENTLY EXIST** - Critical Gap

---

## 📊 Current State Analysis

### Test Coverage: **0%** ❌

| Component | Unit Tests | Integration Tests | E2E Tests | Status |
|-----------|------------|-------------------|-----------|--------|
| Backend API | ❌ 0% | ❌ 0% | ❌ 0% | Not Started |
| Frontend | ❌ 0% | ❌ 0% | ❌ 0% | Not Started |
| Database | ❌ 0% | ❌ 0% | ❌ 0% | Not Started |
| Infrastructure | ❌ 0% | ❌ 0% | ❌ 0% | Not Started |

### Critical Findings

**🚨 BLOCKERS:**
1. No automated tests exist
2. No test framework configured for backend
3. No CI/CD test integration
4. No test data management strategy
5. No performance testing
6. No security testing

**⚠️ HIGH RISK:**
- Manual testing only
- No regression testing
- No API contract testing
- No load testing
- No security scanning

---

## 🎯 QA Strategy

### Phase 1: Foundation (Week 1)
- Set up test frameworks
- Create test data fixtures
- Write critical path tests
- Set up CI/CD integration

### Phase 2: Coverage (Week 2-3)
- Unit tests for all controllers
- Integration tests for API endpoints
- Database migration tests
- Authentication/authorization tests

### Phase 3: Advanced (Week 4)
- E2E tests
- Performance tests
- Security tests
- Load tests

---


## 📋 Test Plan

### 1. Backend API Testing

#### 1.1 Unit Tests (Controllers)

**Target Coverage:** 80%

**Test Files to Create:**
```
server/src/tests/
├── unit/
│   ├── controllers/
│   │   ├── adminController.test.js
│   │   └── customerController.test.js
│   ├── middleware/
│   │   ├── auth.test.js
│   │   ├── validator.test.js
│   │   └── errorHandler.test.js
│   └── utils/
│       └── validation.test.js
```

**Test Scenarios:**

**Admin Controller:**
- ✅ Valid login returns JWT token
- ✅ Invalid credentials return 401
- ✅ Missing email returns 400
- ✅ Missing password returns 400
- ✅ Invalid email format returns 400
- ✅ Token refresh with valid token succeeds
- ✅ Token refresh with expired token fails
- ✅ Token refresh with invalid token fails

**Customer Controller:**
- ✅ Valid registration creates customer
- ✅ Duplicate NIC returns 400
- ✅ Duplicate phone returns 400
- ✅ Invalid NIC format returns 400
- ✅ Invalid phone format returns 400
- ✅ Missing required fields returns 400
- ✅ Fetch customers requires authentication
- ✅ Delete customer requires authentication
- ✅ Delete non-existent customer returns 404
- ✅ Soft delete sets is_deleted flag

---

#### 1.2 Integration Tests (API Endpoints)

**Target Coverage:** 90% of critical paths

**Test Files to Create:**
```
server/src/tests/
├── integration/
│   ├── api/
│   │   ├── admin.integration.test.js
│   │   ├── customers.integration.test.js
│   │   └── health.integration.test.js
│   └── database/
│       ├── connection.test.js
│       └── migrations.test.js
```

**Test Scenarios:**

**Admin API:**
- ✅ POST /api/admin/login - successful login flow
- ✅ POST /api/admin/login - failed login flow
- ✅ POST /api/admin/refresh - token refresh flow
- ✅ Rate limiting on login endpoint

**Customer API:**
- ✅ POST /api/customers/register - full registration flow
- ✅ GET /api/customers - authenticated access
- ✅ GET /api/customers - unauthenticated returns 401
- ✅ DELETE /api/customers/:id - soft delete flow
- ✅ Pagination on customer list
- ✅ Search functionality

**Health Check:**
- ✅ GET /health returns 200
- ✅ Health check includes database status
- ✅ Health check includes memory usage

---

#### 1.3 Database Tests

**Test Files to Create:**
```
server/src/tests/
├── database/
│   ├── schema.test.js
│   ├── migrations.test.js
│   ├── seeds.test.js
│   └── queries.test.js
```

**Test Scenarios:**
- ✅ Schema creation succeeds
- ✅ All indexes exist
- ✅ Foreign key constraints work
- ✅ Unique constraints enforced
- ✅ Default values applied
- ✅ Timestamps auto-populate
- ✅ Soft delete queries work
- ✅ Connection pool handles load

---

### 2. Frontend Testing

#### 2.1 Component Tests

**Test Files to Create:**
```
src/tests/
├── components/
│   ├── Register.test.tsx
│   ├── AdminLogin.test.tsx
│   ├── AdminDashboard.test.tsx
│   └── LoyaltyCard.test.tsx
```

**Test Scenarios:**
- ✅ Registration form renders
- ✅ Form validation works
- ✅ Successful registration shows success message
- ✅ Failed registration shows error
- ✅ Admin login form works
- ✅ Dashboard displays customers
- ✅ Delete customer confirmation works

---

#### 2.2 Integration Tests (Frontend)

**Test Files to Create:**
```
src/tests/
├── integration/
│   ├── registration-flow.test.tsx
│   ├── admin-flow.test.tsx
│   └── api-integration.test.tsx
```

**Test Scenarios:**
- ✅ Complete registration flow
- ✅ Complete admin login flow
- ✅ Customer list pagination
- ✅ Customer deletion flow
- ✅ Token refresh on expiry

---

### 3. End-to-End Tests

#### 3.1 User Journeys

**Test Files to Create:**
```
e2e/
├── customer-registration.spec.js
├── admin-management.spec.js
└── error-scenarios.spec.js
```

**Test Scenarios:**

**Customer Journey:**
1. Navigate to registration page
2. Fill in valid details
3. Submit form
4. Verify success message
5. Verify loyalty number displayed

**Admin Journey:**
1. Navigate to admin login
2. Enter credentials
3. View customer list
4. Search for customer
5. Delete customer
6. Verify deletion

**Error Scenarios:**
1. Network failure handling
2. Session timeout handling
3. Invalid token handling
4. Database connection failure

---

### 4. Performance Testing

#### 4.1 Load Tests

**Test Files to Create:**
```
performance/
├── load-tests/
│   ├── registration-load.js
│   ├── login-load.js
│   └── customer-list-load.js
```

**Test Scenarios:**
- ✅ 100 concurrent registrations
- ✅ 500 concurrent logins
- ✅ 1000 customer list requests
- ✅ Database connection pool under load
- ✅ Response time < 500ms (p95)
- ✅ Error rate < 1%

---

#### 4.2 Stress Tests

**Test Scenarios:**
- ✅ Gradual load increase to breaking point
- ✅ Sustained high load (1 hour)
- ✅ Spike testing (sudden traffic surge)
- ✅ Recovery after overload

---

### 5. Security Testing

#### 5.1 Authentication Tests

**Test Scenarios:**
- ✅ JWT token validation
- ✅ Token expiration handling
- ✅ Invalid token rejection
- ✅ Missing token rejection
- ✅ Token tampering detection
- ✅ Refresh token security

---

#### 5.2 Authorization Tests

**Test Scenarios:**
- ✅ Protected endpoints require auth
- ✅ Role-based access control
- ✅ Horizontal privilege escalation prevention
- ✅ Vertical privilege escalation prevention

---

#### 5.3 Input Validation Tests

**Test Scenarios:**
- ✅ SQL injection attempts blocked
- ✅ XSS attempts blocked
- ✅ Command injection blocked
- ✅ Path traversal blocked
- ✅ Buffer overflow protection
- ✅ Malformed JSON handling

---

#### 5.4 Security Scanning

**Tools to Use:**
- OWASP ZAP
- Snyk
- npm audit
- Trivy (container scanning)

---

### 6. Infrastructure Testing

#### 6.1 Container Tests

**Test Scenarios:**
- ✅ Docker image builds successfully
- ✅ Container starts without errors
- ✅ Health check passes
- ✅ Environment variables loaded
- ✅ Database connection works
- ✅ Logs output correctly

---

#### 6.2 Deployment Tests

**Test Scenarios:**
- ✅ CloudFormation stack deploys
- ✅ ECS tasks start successfully
- ✅ ALB health checks pass
- ✅ RDS connection works
- ✅ Rolling deployment succeeds
- ✅ Rollback works on failure

---

## 🛠️ Test Framework Setup

### Backend Testing Stack

**Recommended Tools:**
```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "@types/jest": "^29.5.11",
    "@types/supertest": "^6.0.2",
    "testcontainers": "^10.5.0",
    "faker": "^5.5.3"
  }
}
```

**Setup Steps:**

1. **Install dependencies:**
```bash
cd server
npm install --save-dev jest supertest @types/jest @types/supertest testcontainers faker
```

2. **Create jest.config.js:**
```javascript
export default {
  testEnvironment: 'node',
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/test/**',
    '!src/**/*.test.js'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.js']
};
```

3. **Update package.json:**
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:integration": "jest --testPathPattern=integration",
    "test:unit": "jest --testPathPattern=unit"
  }
}
```

---

### Frontend Testing Stack

**Already Configured:**
- ✅ Vitest
- ✅ React Testing Library
- ✅ jsdom

**Additional Tools Needed:**
```bash
npm install --save-dev @testing-library/user-event msw
```

---

### E2E Testing Stack

**Recommended: Playwright**

```bash
npm install --save-dev @playwright/test
npx playwright install
```

**Create playwright.config.ts:**
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } }
  ]
});
```

---

### Performance Testing Stack

**Recommended: k6**

```bash
# Install k6
brew install k6  # macOS
# or
choco install k6  # Windows
```

---


## 📝 Test Implementation Guide

### Step 1: Backend Unit Tests (Day 1-2)

#### Create Test Setup File

**File:** `server/src/test/setup.js`
```javascript
import { jest } from '@jest/globals';

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';
process.env.JWT_REFRESH_SECRET = 'test-refresh-secret';
process.env.DB_HOST = 'localhost';
process.env.DB_USER = 'test';
process.env.DB_PASSWORD = 'test';
process.env.DB_NAME = 'singha_loyalty_test';

// Global test timeout
jest.setTimeout(10000);

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
```

---

#### Example: Admin Controller Unit Test

**File:** `server/src/test/unit/controllers/adminController.test.js`
```javascript
import { jest } from '@jest/globals';
import { login, refreshToken } from '../../../controllers/adminController.js';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';

// Mock dependencies
jest.mock('bcryptjs');
jest.mock('jsonwebtoken');
jest.mock('../../../config/database.js', () => ({
  default: {
    query: jest.fn()
  }
}));

describe('Admin Controller', () => {
  let req, res, pool;

  beforeEach(() => {
    req = {
      body: {}
    };
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn()
    };
    
    // Import mocked pool
    pool = require('../../../config/database.js').default;
  });

  describe('login', () => {
    it('should return JWT token on valid credentials', async () => {
      // Arrange
      req.body = {
        email: 'admin@singha.com',
        password: 'Admin@123'
      };

      pool.query.mockResolvedValueOnce([[{
        id: 1,
        email: 'admin@singha.com',
        password_hash: '$2a$10$hashedpassword',
        is_active: 1
      }]]);

      bcrypt.compare.mockResolvedValueOnce(true);
      jwt.sign.mockReturnValueOnce('mock-access-token');
      jwt.sign.mockReturnValueOnce('mock-refresh-token');

      // Act
      await login(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        token: 'mock-access-token',
        refreshToken: 'mock-refresh-token'
      });
    });

    it('should return 401 on invalid credentials', async () => {
      // Arrange
      req.body = {
        email: 'admin@singha.com',
        password: 'WrongPassword'
      };

      pool.query.mockResolvedValueOnce([[{
        id: 1,
        email: 'admin@singha.com',
        password_hash: '$2a$10$hashedpassword',
        is_active: 1
      }]]);

      bcrypt.compare.mockResolvedValueOnce(false);

      // Act
      await login(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({
        error: 'Invalid email or password'
      });
    });

    it('should return 400 on missing email', async () => {
      // Arrange
      req.body = {
        password: 'Admin@123'
      };

      // Act
      await login(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(400);
    });

    it('should return 401 on inactive account', async () => {
      // Arrange
      req.body = {
        email: 'admin@singha.com',
        password: 'Admin@123'
      };

      pool.query.mockResolvedValueOnce([[{
        id: 1,
        email: 'admin@singha.com',
        password_hash: '$2a$10$hashedpassword',
        is_active: 0
      }]]);

      // Act
      await login(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({
        error: 'Account is inactive'
      });
    });
  });

  describe('refreshToken', () => {
    it('should return new tokens on valid refresh token', async () => {
      // Arrange
      req.body = {
        refreshToken: 'valid-refresh-token'
      };

      jwt.verify.mockReturnValueOnce({
        email: 'admin@singha.com',
        userId: 1
      });

      jwt.sign.mockReturnValueOnce('new-access-token');
      jwt.sign.mockReturnValueOnce('new-refresh-token');

      // Act
      await refreshToken(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith({
        success: true,
        token: 'new-access-token',
        refreshToken: 'new-refresh-token'
      });
    });

    it('should return 401 on expired refresh token', async () => {
      // Arrange
      req.body = {
        refreshToken: 'expired-token'
      };

      jwt.verify.mockImplementationOnce(() => {
        const error = new Error('Token expired');
        error.name = 'TokenExpiredError';
        throw error;
      });

      // Act
      await refreshToken(req, res);

      // Assert
      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({
        error: 'Refresh token expired'
      });
    });
  });
});
```

**Run tests:**
```bash
npm test
```

---

### Step 2: Integration Tests (Day 3-4)

#### Example: Customer API Integration Test

**File:** `server/src/test/integration/api/customers.integration.test.js`
```javascript
import request from 'supertest';
import app from '../../../index.js';
import pool from '../../../config/database.js';

describe('Customer API Integration Tests', () => {
  let authToken;

  beforeAll(async () => {
    // Login to get auth token
    const response = await request(app)
      .post('/api/admin/login')
      .send({
        email: 'admin@singha.com',
        password: 'Admin@123'
      });
    
    authToken = response.body.token;
  });

  afterAll(async () => {
    // Clean up test data
    await pool.query('DELETE FROM customers WHERE nic_number LIKE "TEST%"');
    await pool.end();
  });

  describe('POST /api/customers/register', () => {
    it('should register a new customer', async () => {
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: 'TEST123456789V',
          fullName: 'Test Customer',
          phoneNumber: '0771234567'
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('loyaltyNumber');
      expect(response.body.loyaltyNumber).toMatch(/^\d{4}$/);
    });

    it('should reject duplicate NIC', async () => {
      // First registration
      await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: 'TEST987654321V',
          fullName: 'Test Customer',
          phoneNumber: '0771234567'
        });

      // Duplicate registration
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: 'TEST987654321V',
          fullName: 'Another Customer',
          phoneNumber: '0779876543'
        })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('already registered');
    });

    it('should validate NIC format', async () => {
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: 'INVALID',
          fullName: 'Test Customer',
          phoneNumber: '0771234567'
        })
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    it('should validate phone format', async () => {
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: 'TEST111222333V',
          fullName: 'Test Customer',
          phoneNumber: 'invalid-phone'
        })
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /api/customers', () => {
    it('should require authentication', async () => {
      await request(app)
        .get('/api/customers')
        .expect(401);
    });

    it('should return customer list with valid token', async () => {
      const response = await request(app)
        .get('/api/customers')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body).toHaveProperty('customers');
      expect(Array.isArray(response.body.customers)).toBe(true);
    });

    it('should reject invalid token', async () => {
      await request(app)
        .get('/api/customers')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });
  });

  describe('DELETE /api/customers/:id', () => {
    let customerId;

    beforeEach(async () => {
      // Create test customer
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: `TEST${Date.now()}V`,
          fullName: 'Delete Test',
          phoneNumber: '0771234567'
        });

      // Get customer ID
      const [rows] = await pool.query(
        'SELECT id FROM customers WHERE loyalty_number = ?',
        [response.body.loyaltyNumber]
      );
      customerId = rows[0].id;
    });

    it('should soft delete customer', async () => {
      await request(app)
        .delete(`/api/customers/${customerId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      // Verify soft delete
      const [rows] = await pool.query(
        'SELECT is_deleted FROM customers WHERE id = ?',
        [customerId]
      );
      expect(rows[0].is_deleted).toBe(1);
    });

    it('should require authentication', async () => {
      await request(app)
        .delete(`/api/customers/${customerId}`)
        .expect(401);
    });

    it('should return 404 for non-existent customer', async () => {
      await request(app)
        .delete('/api/customers/999999')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);
    });
  });
});
```

**Run integration tests:**
```bash
npm run test:integration
```

---

### Step 3: E2E Tests (Day 5-6)

#### Example: Customer Registration E2E Test

**File:** `e2e/customer-registration.spec.js`
```javascript
import { test, expect } from '@playwright/test';

test.describe('Customer Registration Flow', () => {
  test('should complete full registration flow', async ({ page }) => {
    // Navigate to registration page
    await page.goto('/register');

    // Verify page loaded
    await expect(page.locator('h1')).toContainText('Register');

    // Fill in form
    await page.fill('[name="nicNumber"]', '123456789V');
    await page.fill('[name="fullName"]', 'John Doe');
    await page.fill('[name="phoneNumber"]', '0771234567');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for success message
    await expect(page.locator('.success-message')).toBeVisible();

    // Verify loyalty number displayed
    const loyaltyNumber = await page.locator('.loyalty-number').textContent();
    expect(loyaltyNumber).toMatch(/^\d{4}$/);

    // Verify redirect to success page
    await expect(page).toHaveURL('/register/success');
  });

  test('should show validation errors', async ({ page }) => {
    await page.goto('/register');

    // Submit empty form
    await page.click('button[type="submit"]');

    // Verify error messages
    await expect(page.locator('.error-message')).toHaveCount(3);
  });

  test('should handle duplicate registration', async ({ page }) => {
    await page.goto('/register');

    // Use existing NIC
    await page.fill('[name="nicNumber"]', '123456789V');
    await page.fill('[name="fullName"]', 'Jane Doe');
    await page.fill('[name="phoneNumber"]', '0779876543');

    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.locator('.error-message'))
      .toContainText('already registered');
  });
});
```

**Run E2E tests:**
```bash
npx playwright test
```

---


### Step 4: Performance Tests (Day 7)

#### Example: Load Test with k6

**File:** `performance/load-tests/registration-load.js`
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 users
    { duration: '3m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.01'],             // Error rate under 1%
  },
};

export default function () {
  const url = 'http://localhost:3000/api/customers/register';
  
  const payload = JSON.stringify({
    nicNumber: `${Math.floor(Math.random() * 1000000000)}V`,
    fullName: `Test User ${Math.random()}`,
    phoneNumber: `077${Math.floor(Math.random() * 10000000)}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post(url, payload, params);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has loyalty number': (r) => JSON.parse(r.body).loyaltyNumber !== undefined,
  });

  errorRate.add(!success);

  sleep(1);
}
```

**Run load test:**
```bash
k6 run performance/load-tests/registration-load.js
```

---

### Step 5: Security Tests (Day 8)

#### Example: Security Test Suite

**File:** `server/src/test/security/auth.security.test.js`
```javascript
import request from 'supertest';
import app from '../../index.js';

describe('Security Tests - Authentication', () => {
  describe('SQL Injection Prevention', () => {
    it('should prevent SQL injection in login', async () => {
      const response = await request(app)
        .post('/api/admin/login')
        .send({
          email: "admin@singha.com' OR '1'='1",
          password: "' OR '1'='1"
        });

      expect(response.status).toBe(401);
    });

    it('should prevent SQL injection in customer search', async () => {
      const response = await request(app)
        .get('/api/customers?search=\' OR 1=1--')
        .set('Authorization', 'Bearer valid-token');

      expect(response.status).not.toBe(500);
    });
  });

  describe('XSS Prevention', () => {
    it('should sanitize customer name input', async () => {
      const response = await request(app)
        .post('/api/customers/register')
        .send({
          nicNumber: '123456789V',
          fullName: '<script>alert("XSS")</script>',
          phoneNumber: '0771234567'
        });

      if (response.status === 200) {
        expect(response.body.fullName).not.toContain('<script>');
      }
    });
  });

  describe('JWT Security', () => {
    it('should reject tampered JWT', async () => {
      const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFkbWluQHNpbmdoYS5jb20iLCJyb2xlIjoiYWRtaW4ifQ.tampered';

      await request(app)
        .get('/api/customers')
        .set('Authorization', `Bearer ${tamperedToken}`)
        .expect(401);
    });

    it('should reject expired JWT', async () => {
      // Create expired token
      const expiredToken = jwt.sign(
        { email: 'admin@singha.com' },
        process.env.JWT_SECRET,
        { expiresIn: '-1h' }
      );

      await request(app)
        .get('/api/customers')
        .set('Authorization', `Bearer ${expiredToken}`)
        .expect(401);
    });

    it('should reject JWT with wrong signature', async () => {
      const wrongToken = jwt.sign(
        { email: 'admin@singha.com' },
        'wrong-secret'
      );

      await request(app)
        .get('/api/customers')
        .set('Authorization', `Bearer ${wrongToken}`)
        .expect(401);
    });
  });

  describe('Rate Limiting', () => {
    it('should rate limit login attempts', async () => {
      const requests = [];

      // Make 10 rapid login attempts
      for (let i = 0; i < 10; i++) {
        requests.push(
          request(app)
            .post('/api/admin/login')
            .send({
              email: 'admin@singha.com',
              password: 'wrong-password'
            })
        );
      }

      const responses = await Promise.all(requests);
      const rateLimited = responses.some(r => r.status === 429);

      expect(rateLimited).toBe(true);
    });
  });

  describe('CORS Security', () => {
    it('should reject requests from unauthorized origins', async () => {
      const response = await request(app)
        .get('/api/customers')
        .set('Origin', 'http://malicious-site.com')
        .set('Authorization', 'Bearer valid-token');

      expect(response.headers['access-control-allow-origin']).not.toBe('http://malicious-site.com');
    });
  });
});
```

---

## 📊 Test Execution Plan

### Week 1: Foundation

**Day 1-2: Setup & Unit Tests**
- [ ] Install test frameworks
- [ ] Configure Jest
- [ ] Write admin controller tests
- [ ] Write customer controller tests
- [ ] Write middleware tests
- [ ] Target: 50% unit test coverage

**Day 3-4: Integration Tests**
- [ ] Set up test database
- [ ] Write API integration tests
- [ ] Write database tests
- [ ] Target: 70% integration coverage

**Day 5-6: E2E Tests**
- [ ] Install Playwright
- [ ] Write customer journey tests
- [ ] Write admin journey tests
- [ ] Write error scenario tests
- [ ] Target: Critical paths covered

**Day 7: Performance Tests**
- [ ] Install k6
- [ ] Write load tests
- [ ] Write stress tests
- [ ] Establish baselines

**Day 8: Security Tests**
- [ ] Write security test suite
- [ ] Run OWASP ZAP scan
- [ ] Run npm audit
- [ ] Run Snyk scan

---

## 🎯 Test Coverage Goals

### Minimum Acceptable Coverage

| Type | Target | Critical |
|------|--------|----------|
| Unit Tests | 70% | 90% |
| Integration Tests | 60% | 80% |
| E2E Tests | Critical Paths | 100% |
| API Endpoints | 80% | 100% |

### Coverage by Component

```
server/src/
├── controllers/        Target: 90%
├── middleware/         Target: 85%
├── routes/            Target: 100%
├── config/            Target: 70%
└── utils/             Target: 80%
```

---

## 🔍 Test Data Management

### Test Database Setup

**File:** `server/src/test/database/setup.js`
```javascript
import mysql from 'mysql2/promise';
import fs from 'fs';

export async function setupTestDatabase() {
  const connection = await mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'root'
  });

  // Create test database
  await connection.query('CREATE DATABASE IF NOT EXISTS singha_loyalty_test');
  await connection.query('USE singha_loyalty_test');

  // Run schema
  const schema = fs.readFileSync('./src/db/schema.sql', 'utf8');
  await connection.query(schema);

  await connection.end();
}

export async function teardownTestDatabase() {
  const connection = await mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'root'
  });

  await connection.query('DROP DATABASE IF EXISTS singha_loyalty_test');
  await connection.end();
}

export async function seedTestData() {
  const pool = mysql.createPool({
    host: 'localhost',
    user: 'root',
    password: 'root',
    database: 'singha_loyalty_test'
  });

  // Insert test admin
  await pool.query(`
    INSERT INTO admins (email, password_hash, full_name)
    VALUES ('test@admin.com', '$2a$10$test', 'Test Admin')
  `);

  // Insert test customers
  await pool.query(`
    INSERT INTO customers (nic_number, full_name, phone_number, loyalty_number)
    VALUES 
      ('TEST123V', 'Test Customer 1', '0771111111', '1001'),
      ('TEST456V', 'Test Customer 2', '0772222222', '1002')
  `);

  await pool.end();
}
```

---

### Test Fixtures

**File:** `server/src/test/fixtures/customers.js`
```javascript
export const validCustomer = {
  nicNumber: '123456789V',
  fullName: 'John Doe',
  phoneNumber: '0771234567'
};

export const invalidNIC = {
  nicNumber: 'INVALID',
  fullName: 'John Doe',
  phoneNumber: '0771234567'
};

export const invalidPhone = {
  nicNumber: '123456789V',
  fullName: 'John Doe',
  phoneNumber: 'invalid'
};

export const duplicateCustomer = {
  nicNumber: '123456789V', // Already exists
  fullName: 'Jane Doe',
  phoneNumber: '0779876543'
};
```

---

## 🚀 CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: singha_loyalty_test
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd server
          npm ci

      - name: Run unit tests
        run: |
          cd server
          npm run test:unit

      - name: Run integration tests
        run: |
          cd server
          npm run test:integration
        env:
          DB_HOST: 127.0.0.1
          DB_USER: root
          DB_PASSWORD: root
          DB_NAME: singha_loyalty_test

      - name: Generate coverage report
        run: |
          cd server
          npm run test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./server/coverage/lcov.info

      - name: Run E2E tests
        run: |
          npx playwright test

      - name: Run security scan
        run: |
          npm audit
          npx snyk test
```

---

ml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: singha_loyalty_test
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: ./server
        run: npm ci
      
      - name: Run tests
        working-directory: ./server
        run: npm test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📈 Test Metrics & Reporting

### Key Metrics to Track

1. **Test Coverage**
   - Line coverage
   - Branch coverage
   - Function coverage
   - Statement coverage

2. **Test Execution**
   - Total tests
   - Passing tests
   - Failing tests
   - Skipped tests
   - Execution time

3. **Quality Metrics**
   - Defect detection rate
   - Test flakiness rate
   - Mean time to detect (MTTD)
   - Mean time to resolve (MTTR)

4. **Performance Metrics**
   - Response time (p50, p95, p99)
   - Throughput (requests/second)
   - Error rate
   - Resource utilization

---

### Reporting Tools

**Coverage Reports:**
```bash
# Generate HTML coverage report
npm run test:coverage

# View report
open coverage/lcov-report/index.html
```

**Test Results:**
```bash
# Generate JUnit XML report
npm test -- --reporters=default --reporters=jest-junit

# View in CI/CD dashboard
```

**Performance Reports:**
```bash
# k6 generates HTML report
k6 run --out json=results.json performance/load-tests/registration-load.js

# Convert to HTML
k6 report results.json
```

---

## 🎯 Test Prioritization Matrix

### Priority 1: Critical (Must Test)
- User authentication
- Customer registration
- Payment processing (if applicable)
- Data integrity
- Security vulnerabilities

### Priority 2: High (Should Test)
- Customer list/search
- Admin dashboard
- Data validation
- Error handling
- API endpoints

### Priority 3: Medium (Nice to Test)
- UI components
- Edge cases
- Performance optimization
- Accessibility
- Browser compatibility

### Priority 4: Low (Optional)
- Visual regression
- Localization
- Advanced features
- Nice-to-have functionality

---

## 🔄 Test Maintenance Strategy

### Weekly Tasks
- [ ] Review failed tests
- [ ] Fix flaky tests
- [ ] Update test data
- [ ] Check coverage trends

### Monthly Tasks
- [ ] Review test suite performance
- [ ] Refactor slow tests
- [ ] Update dependencies
- [ ] Security scan review

### Quarterly Tasks
- [ ] Comprehensive test audit
- [ ] Update test strategy
- [ ] Performance baseline review
- [ ] Team training session

---

## 🚨 Test Failure Protocol

### When Tests Fail

1. **Immediate Actions**
   - Check if it's a real bug or flaky test
   - Review recent code changes
   - Check CI/CD logs
   - Verify test environment

2. **Investigation**
   - Reproduce locally
   - Check test data
   - Review error messages
   - Analyze stack traces

3. **Resolution**
   - Fix the bug (if real issue)
   - Fix the test (if test issue)
   - Update test data (if data issue)
   - Document the fix

4. **Prevention**
   - Add regression test
   - Update documentation
   - Share learnings with team
   - Improve test coverage

---

## 📚 Test Data Management

### Test Data Strategy

**Fixtures:**
```javascript
// server/src/test/fixtures/customers.js
export const validCustomer = {
  nicNumber: '123456789V',
  fullName: 'John Doe',
  phoneNumber: '0771234567'
};

export const invalidCustomers = [
  { nicNumber: 'INVALID', fullName: 'Test', phoneNumber: '0771234567' },
  { nicNumber: '123456789V', fullName: '', phoneNumber: '0771234567' },
  { nicNumber: '123456789V', fullName: 'Test', phoneNumber: 'invalid' }
];
```

**Factories:**
```javascript
// server/src/test/factories/customerFactory.js
import { faker } from '@faker-js/faker';

export function createCustomer(overrides = {}) {
  return {
    nicNumber: faker.string.numeric(9) + 'V',
    fullName: faker.person.fullName(),
    phoneNumber: '077' + faker.string.numeric(7),
    ...overrides
  };
}

export function createCustomers(count = 10) {
  return Array.from({ length: count }, () => createCustomer());
}
```

**Database Seeding:**
```javascript
// server/src/test/helpers/seed.js
export async function seedTestData(pool) {
  // Insert test admin
  await pool.query(`
    INSERT INTO admins (email, password_hash, full_name)
    VALUES ('test@admin.com', '$2a$10$test', 'Test Admin')
  `);

  // Insert test customers
  const customers = createCustomers(50);
  for (const customer of customers) {
    await pool.query(`
      INSERT INTO customers (nic_number, full_name, phone_number, loyalty_number)
      VALUES (?, ?, ?, ?)
    `, [customer.nicNumber, customer.fullName, customer.phoneNumber, generateLoyaltyNumber()]);
  }
}
```

---

## 🔐 Security Testing Checklist

### Authentication & Authorization
- [ ] JWT token validation
- [ ] Token expiration handling
- [ ] Invalid token rejection
- [ ] Missing token rejection
- [ ] Token tampering detection
- [ ] Refresh token security
- [ ] Session management
- [ ] Password hashing (bcrypt)
- [ ] Brute force protection
- [ ] Account lockout

### Input Validation
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Command injection prevention
- [ ] Path traversal prevention
- [ ] File upload validation
- [ ] JSON parsing security
- [ ] XML external entity (XXE) prevention
- [ ] LDAP injection prevention

### API Security
- [ ] CORS configuration
- [ ] Rate limiting
- [ ] Request size limits
- [ ] HTTPS enforcement
- [ ] Security headers (Helmet)
- [ ] API versioning
- [ ] Error message sanitization
- [ ] Sensitive data exposure

### Infrastructure Security
- [ ] Container security (Trivy scan)
- [ ] Dependency vulnerabilities (npm audit, Snyk)
- [ ] Secrets management
- [ ] Network security
- [ ] Database security
- [ ] Logging and monitoring
- [ ] Backup and recovery

---

## 🎭 Test Environment Strategy

### Environments

**Local Development:**
- Purpose: Developer testing
- Database: Local MySQL
- Data: Minimal test data
- Refresh: On demand

**CI/CD:**
- Purpose: Automated testing
- Database: Docker MySQL
- Data: Fresh on each run
- Refresh: Every commit

**Staging:**
- Purpose: Pre-production testing
- Database: RDS (small instance)
- Data: Production-like data
- Refresh: Weekly

**Production:**
- Purpose: Live system
- Database: RDS (production instance)
- Data: Real customer data
- Refresh: N/A

---

## 📊 Test Coverage Report Example

```
File                          | % Stmts | % Branch | % Funcs | % Lines |
------------------------------|---------|----------|---------|---------|
All files                     |   78.45 |    72.31 |   81.25 |   78.92 |
 controllers                  |   85.67 |    78.45 |   90.12 |   86.34 |
  adminController.js          |   92.31 |    85.71 |   100.0 |   93.75 |
  customerController.js       |   81.25 |    73.33 |   83.33 |   82.14 |
 middleware                   |   88.23 |    82.14 |   87.50 |   89.47 |
  auth.js                     |   95.45 |    90.00 |   100.0 |   96.15 |
  validator.js                |   80.00 |    75.00 |   75.00 |   81.25 |
  errorHandler.js             |   90.00 |    81.25 |   87.50 |   91.67 |
 routes                       |   100.0 |    100.0 |   100.0 |   100.0 |
  admin.js                    |   100.0 |    100.0 |   100.0 |   100.0 |
  customers.js                |   100.0 |    100.0 |   100.0 |   100.0 |
 config                       |   65.00 |    50.00 |   60.00 |   66.67 |
  database.js                 |   65.00 |    50.00 |   60.00 |   66.67 |
```

---

## 🎯 QA Best Practices

### Test Writing
1. **Follow AAA pattern** (Arrange, Act, Assert)
2. **One assertion per test** (when possible)
3. **Descriptive test names** (should do X when Y)
4. **Independent tests** (no test dependencies)
5. **Fast tests** (< 1 second per unit test)
6. **Deterministic tests** (no random failures)

### Test Organization
1. **Group related tests** (describe blocks)
2. **Use setup/teardown** (beforeEach, afterEach)
3. **Share test utilities** (helpers, fixtures)
4. **Consistent naming** (*.test.js, *.spec.js)
5. **Clear directory structure** (unit, integration, e2e)

### Test Maintenance
1. **Fix flaky tests immediately**
2. **Remove obsolete tests**
3. **Refactor duplicate code**
4. **Update test data regularly**
5. **Review coverage trends**
6. **Keep tests simple**

---

## 🚀 Continuous Improvement

### Quarterly Review

**Questions to Ask:**
1. Is our test coverage adequate?
2. Are tests catching bugs before production?
3. Are tests running fast enough?
4. Are there too many flaky tests?
5. Is the test suite maintainable?
6. Are we testing the right things?

**Actions to Take:**
1. Analyze defect escape rate
2. Review test execution time
3. Identify and fix flaky tests
4. Update test strategy
5. Train team on new practices
6. Invest in test infrastructure

---

## 📞 QA Team Contacts

**QA Lead:** [Your Name]
**Email:** qa-team@company.com
**Slack:** #qa-team
**Office Hours:** Mon-Fri 9am-5pm

**Escalation Path:**
1. QA Engineer
2. QA Lead
3. Engineering Manager
4. CTO

---

## 📖 Additional Resources

### Documentation
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [k6 Documentation](https://k6.io/docs/)
- [Testing Library](https://testing-library.com/)

### Training
- Testing JavaScript (Kent C. Dodds)
- Test Automation University
- Playwright Learning Path
- Performance Testing with k6

### Tools
- Jest - Unit/Integration testing
- Playwright - E2E testing
- k6 - Performance testing
- Snyk - Security scanning
- OWASP ZAP - Security testing
- Codecov - Coverage reporting

---

## ✅ Final Checklist

### Before Deployment
- [ ] All tests passing
- [ ] Coverage > 65%
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks met
- [ ] E2E tests passing
- [ ] Load tests completed
- [ ] Security scans clean
- [ ] Documentation updated

### After Deployment
- [ ] Smoke tests passed
- [ ] Monitoring alerts configured
- [ ] Error tracking enabled
- [ ] Performance monitoring active
- [ ] Backup verified
- [ ] Rollback plan tested

---

## 🎉 Conclusion

This QA strategy provides a comprehensive approach to testing the Singha Loyalty System. By following this guide, you will:

✅ Achieve 80%+ test coverage
✅ Catch bugs before production
✅ Ensure security and performance
✅ Build confidence in deployments
✅ Maintain high code quality
✅ Enable continuous delivery

**Remember:** Testing is not a one-time activity. It's an ongoing process that requires continuous attention and improvement.

**Next Steps:**
1. Review QA_IMPLEMENTATION_GUIDE.md
2. Start with Week 1 tasks
3. Track progress daily
4. Adjust strategy as needed
5. Celebrate wins! 🎉

---

**Document Version:** 1.0
**Last Updated:** January 31, 2026
**Status:** Ready for Implementation
**Owner:** Senior QA Engineer

Good luck with your testing journey! 🚀
