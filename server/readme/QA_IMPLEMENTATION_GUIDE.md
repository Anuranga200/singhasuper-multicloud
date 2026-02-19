# QA Implementation Guide - Step by Step

## 🎯 Your Mission: Implement Complete Test Coverage

**Current Status:** 0% test coverage ❌
**Target Status:** 80% test coverage ✅
**Timeline:** 2 weeks
**Effort:** ~80 hours

---

## 📅 2-Week Implementation Plan

### Week 1: Backend Testing

#### Day 1: Setup (4 hours)

**Morning (2 hours): Install & Configure**

1. **Install test dependencies:**
```bash
cd server
npm install --save-dev \
  jest \
  @types/jest \
  supertest \
  @types/supertest \
  faker \
  testcontainers
```

2. **Create jest.config.js:**
```bash
cat > jest.config.js << 'EOF'
export default {
  testEnvironment: 'node',
  transform: {},
  extensionsToTreatAsEsm: ['.js'],
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/test/**',
    '!src/**/*.test.js'
  ],
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ]
};
EOF
```

3. **Update package.json scripts:**
```json
{
  "scripts": {
    "test": "NODE_OPTIONS=--experimental-vm-modules jest",
    "test:watch": "NODE_OPTIONS=--experimental-vm-modules jest --watch",
    "test:coverage": "NODE_OPTIONS=--experimental-vm-modules jest --coverage",
    "test:unit": "NODE_OPTIONS=--experimental-vm-modules jest --testPathPattern=unit",
    "test:integration": "NODE_OPTIONS=--experimental-vm-modules jest --testPathPattern=integration"
  }
}
```

**Afternoon (2 hours): Create Test Structure**

4. **Create test directories:**
```bash
mkdir -p src/test/{unit,integration,fixtures,helpers}
mkdir -p src/test/unit/{controllers,middleware,utils}
mkdir -p src/test/integration/{api,database}
```

5. **Create test setup file:**
```bash
cat > src/test/setup.js << 'EOF'
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-jwt-secret-key-12345';
process.env.JWT_REFRESH_SECRET = 'test-refresh-secret-key-12345';
process.env.DB_HOST = 'localhost';
process.env.DB_USER = 'root';
process.env.DB_PASSWORD = 'root';
process.env.DB_NAME = 'singha_loyalty_test';

global.beforeAll(() => {
  console.log('🧪 Starting test suite...');
});

global.afterAll(() => {
  console.log('✅ Test suite completed');
});
EOF
```

6. **Verify setup:**
```bash
npm test -- --version
```

---

#### Day 2: Unit Tests - Controllers (6 hours)

**Task: Write tests for adminController.js**

1. **Create test file:**
```bash
touch src/test/unit/controllers/adminController.test.js
```

2. **Write login tests** (see QA_STRATEGY.md for full code)

3. **Run tests:**
```bash
npm run test:unit
```

4. **Check coverage:**
```bash
npm run test:coverage
```

**Expected Output:**
```
PASS  src/test/unit/controllers/adminController.test.js
  Admin Controller
    login
      ✓ should return JWT token on valid credentials
      ✓ should return 401 on invalid credentials
      ✓ should return 400 on missing email
      ✓ should return 401 on inactive account

Test Suites: 1 passed, 1 total
Tests:       4 passed, 4 total
Coverage:    45% (adminController.js)
```

---

#### Day 3: Unit Tests - More Controllers (6 hours)

**Task: Write tests for customerController.js**

1. **Create test file:**
```bash
touch src/test/unit/controllers/customerController.test.js
```

2. **Write tests for:**
   - registerCustomer()
   - fetchCustomers()
   - deleteCustomer()

3. **Run tests:**
```bash
npm run test:unit
```

**Target:** 70% controller coverage

---

#### Day 4: Unit Tests - Middleware (4 hours)

**Task: Test all middleware**

1. **Create test files:**
```bash
touch src/test/unit/middleware/auth.test.js
touch src/test/unit/middleware/validator.test.js
touch src/test/unit/middleware/errorHandler.test.js
```

2. **Write tests for:**
   - JWT authentication
   - Input validation
   - Error handling

3. **Run tests:**
```bash
npm run test:unit
```

**Target:** 80% middleware coverage

---

#### Day 5: Integration Tests - Setup (4 hours)

**Task: Set up test database**

1. **Create database helper:**
```bash
cat > src/test/helpers/database.js << 'EOF'
import mysql from 'mysql2/promise';
import fs from 'fs';

export async function setupTestDB() {
  const connection = await mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'root'
  });

  await connection.query('DROP DATABASE IF EXISTS singha_loyalty_test');
  await connection.query('CREATE DATABASE singha_loyalty_test');
  await connection.query('USE singha_loyalty_test');

  const schema = fs.readFileSync('./src/db/schema.sql', 'utf8');
  const statements = schema.split(';').filter(s => s.trim());
  
  for (const statement of statements) {
    if (statement.trim()) {
      await connection.query(statement);
    }
  }

  await connection.end();
}

export async function teardownTestDB() {
  const connection = await mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'root'
  });

  await connection.query('DROP DATABASE IF EXISTS singha_loyalty_test');
  await connection.end();
}

export async function cleanTestData() {
  const pool = mysql.createPool({
    host: 'localhost',
    user: 'root',
    password: 'root',
    database: 'singha_loyalty_test'
  });

  await pool.query('DELETE FROM customers WHERE nic_number LIKE "TEST%"');
  await pool.query('DELETE FROM admins WHERE email LIKE "test%"');
  
  await pool.end();
}
EOF
```

2. **Test database setup:**
```bash
node -e "import('./src/test/helpers/database.js').then(m => m.setupTestDB())"
```

---

#### Day 6-7: Integration Tests - API (12 hours)

**Task: Write API integration tests**

1. **Create test files:**
```bash
touch src/test/integration/api/admin.integration.test.js
touch src/test/integration/api/customers.integration.test.js
touch src/test/integration/api/health.integration.test.js
```

2. **Write full API tests** (see QA_STRATEGY.md for examples)

3. **Run integration tests:**
```bash
npm run test:integration
```

**Target:** 80% API coverage

---

### Week 2: Frontend & E2E Testing

#### Day 8: Frontend Unit Tests (6 hours)

**Task: Test React components**

1. **Verify Vitest is configured:**
```bash
cd ..  # Back to root
npm test -- --version
```

2. **Create component tests:**
```bash
mkdir -p src/test/components
touch src/test/components/Register.test.tsx
touch src/test/components/AdminLogin.test.tsx
touch src/test/components/AdminDashboard.test.tsx
```

3. **Example: Register component test:**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Register from '@/pages/Register';

describe('Register Component', () => {
  it('renders registration form', () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/NIC Number/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Phone Number/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    const submitButton = screen.getByRole('button', { name: /register/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/NIC number is required/i)).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const mockRegister = vi.fn().mockResolvedValue({
      success: true,
      loyaltyNumber: '1234'
    });

    render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );

    fireEvent.change(screen.getByLabelText(/NIC Number/i), {
      target: { value: '123456789V' }
    });
    fireEvent.change(screen.getByLabelText(/Full Name/i), {
      target: { value: 'John Doe' }
    });
    fireEvent.change(screen.getByLabelText(/Phone Number/i), {
      target: { value: '0771234567' }
    });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText(/1234/)).toBeInTheDocument();
    });
  });
});
```

4. **Run frontend tests:**
```bash
npm test
```

---

#### Day 9-10: E2E Tests Setup (12 hours)

**Task: Install and configure Playwright**

1. **Install Playwright:**
```bash
npm install --save-dev @playwright/test
npx playwright install
```

2. **Create Playwright config:**
```bash
cat > playwright.config.ts << 'EOF'
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:8080',
    reuseExistingServer: !process.env.CI,
  },
});
EOF
```

3. **Create E2E test directory:**
```bash
mkdir -p e2e
```

4. **Write E2E tests:**
```bash
touch e2e/customer-registration.spec.ts
touch e2e/admin-dashboard.spec.ts
touch e2e/error-handling.spec.ts
```

5. **Example: Customer registration E2E:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Customer Registration Flow', () => {
  test('complete registration successfully', async ({ page }) => {
    await page.goto('/register');

    // Fill form
    await page.fill('[name="nicNumber"]', '123456789V');
    await page.fill('[name="fullName"]', 'John Doe');
    await page.fill('[name="phoneNumber"]', '0771234567');

    // Submit
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('.success-message')).toBeVisible();
    await expect(page.locator('.loyalty-number')).toContainText(/\d{4}/);
  });

  test('show validation errors', async ({ page }) => {
    await page.goto('/register');

    // Submit empty form
    await page.click('button[type="submit"]');

    // Verify errors
    await expect(page.locator('.error-message')).toHaveCount(3);
  });

  test('handle duplicate NIC', async ({ page }) => {
    await page.goto('/register');

    // Use existing NIC
    await page.fill('[name="nicNumber"]', '123456789V');
    await page.fill('[name="fullName"]', 'Jane Doe');
    await page.fill('[name="phoneNumber"]', '0779876543');

    await page.click('button[type="submit"]');

    // Verify error
    await expect(page.locator('.error-message'))
      .toContainText(/already registered/i);
  });
});
```

6. **Run E2E tests:**
```bash
npx playwright test
```

7. **View test report:**
```bash
npx playwright show-report
```

---

#### Day 11: Performance Testing (6 hours)

**Task: Set up and run load tests**

1. **Install k6:**
```bash
# macOS
brew install k6

# Windows
choco install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

2. **Create performance test directory:**
```bash
mkdir -p performance/load-tests
```

3. **Write load tests:**
```bash
cat > performance/load-tests/registration-load.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    errors: ['rate<0.01'],
  },
};

export default function () {
  const url = 'http://localhost:3000/api/customers/register';
  
  const payload = JSON.stringify({
    nicNumber: `${Math.floor(Math.random() * 1000000000)}V`,
    fullName: `Load Test User ${Math.random()}`,
    phoneNumber: `077${Math.floor(Math.random() * 10000000)}`,
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
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
EOF
```

4. **Run load test:**
```bash
k6 run performance/load-tests/registration-load.js
```

5. **Analyze results:**
```
scenarios: (100.00%) 1 scenario, 100 max VUs, 4m30s max duration
✓ status is 200
✓ response time < 500ms
✓ has loyalty number

checks.........................: 100.00% ✓ 15000 ✗ 0
data_received..................: 3.0 MB  12 kB/s
data_sent......................: 2.5 MB  10 kB/s
http_req_duration..............: avg=245ms min=120ms med=230ms max=480ms p(95)=420ms
http_reqs......................: 5000    20/s
```

---

#### Day 12: Security Testing (6 hours)

**Task: Run security scans**

1. **Run npm audit:**
```bash
cd server
npm audit
npm audit fix
```

2. **Install and run Snyk:**
```bash
npm install -g snyk
snyk auth
snyk test
snyk monitor
```

3. **Run OWASP ZAP scan:**
```bash
# Download OWASP ZAP
# https://www.zaproxy.org/download/

# Run baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000 \
  -r zap-report.html
```

4. **Create security test suite:**
```bash
touch src/test/security/auth.security.test.js
touch src/test/security/injection.security.test.js
touch src/test/security/xss.security.test.js
```

5. **Run security tests:**
```bash
npm run test -- --testPathPattern=security
```

---

#### Day 13-14: CI/CD Integration & Documentation (12 hours)

**Task: Integrate tests into CI/CD**

1. **Create GitHub Actions workflow:**
```bash
mkdir -p .github/workflows
cat > .github/workflows/test.yml << 'EOF'
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
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
          cache: 'npm'
          cache-dependency-path: server/package-lock.json
      
      - name: Install dependencies
        working-directory: ./server
        run: npm ci
      
      - name: Run unit tests
        working-directory: ./server
        run: npm run test:unit
      
      - name: Run integration tests
        working-directory: ./server
        run: npm run test:integration
        env:
          DB_HOST: 127.0.0.1
          DB_USER: root
          DB_PASSWORD: root
          DB_NAME: singha_loyalty_test
      
      - name: Generate coverage report
        working-directory: ./server
        run: npm run test:coverage
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./server/coverage/lcov.info
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
EOF
```

2. **Create test documentation:**
```bash
cat > TESTING.md << 'EOF'
# Testing Guide

## Running Tests

### Backend Tests
```bash
cd server

# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# With coverage
npm run test:coverage
```

### Frontend Tests
```bash
# All tests
npm test

# Watch mode
npm run test:watch
```

### E2E Tests
```bash
# All browsers
npx playwright test

# Specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug

# View report
npx playwright show-report
```

### Performance Tests
```bash
k6 run performance/load-tests/registration-load.js
```

### Security Tests
```bash
# npm audit
npm audit

# Snyk scan
snyk test

# Security test suite
npm test -- --testPathPattern=security
```

## Test Coverage

Current coverage: [Update after implementation]

Target coverage:
- Unit tests: 70%
- Integration tests: 60%
- E2E tests: Critical paths
- Overall: 65%

## Writing Tests

### Unit Test Example
```javascript
describe('Component', () => {
  it('should do something', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = doSomething(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

### Integration Test Example
```javascript
describe('API Endpoint', () => {
  it('should return data', async () => {
    const response = await request(app)
      .get('/api/endpoint')
      .expect(200);
    
    expect(response.body).toHaveProperty('data');
  });
});
```

## CI/CD Integration

Tests run automatically on:
- Every push to main/develop
- Every pull request
- Before deployment

## Troubleshooting

### Tests failing locally
1. Check database is running
2. Verify environment variables
3. Clear test database
4. Update dependencies

### Tests passing locally but failing in CI
1. Check CI environment variables
2. Verify database service is running
3. Check Node.js version matches
4. Review CI logs

## Resources

- Jest: https://jestjs.io/
- Playwright: https://playwright.dev/
- k6: https://k6.io/docs/
- Testing Library: https://testing-library.com/
EOF
```

3. **Update README with testing info:**
```bash
cat >> README.md << 'EOF'

## Testing

This project has comprehensive test coverage including:
- Unit tests (Jest)
- Integration tests (Supertest)
- E2E tests (Playwright)
- Performance tests (k6)
- Security tests (Snyk, OWASP ZAP)

See [TESTING.md](TESTING.md) for detailed testing guide.

### Quick Start

```bash
# Backend tests
cd server && npm test

# Frontend tests
npm test

# E2E tests
npx playwright test
```

### Coverage

Current test coverage: 80%+

View coverage report:
```bash
cd server && npm run test:coverage
open coverage/lcov-report/index.html
```
EOF
```

---

## ✅ Completion Checklist

### Week 1: Backend
- [ ] Test framework installed and configured
- [ ] Unit tests for controllers (70%+ coverage)
- [ ] Unit tests for middleware (80%+ coverage)
- [ ] Integration tests for API endpoints (80%+ coverage)
- [ ] Database tests
- [ ] Test database setup/teardown working
- [ ] All backend tests passing

### Week 2: Frontend & E2E
- [ ] Frontend component tests
- [ ] Playwright installed and configured
- [ ] E2E tests for critical user journeys
- [ ] Performance tests with k6
- [ ] Security scans completed
- [ ] CI/CD pipeline configured
- [ ] Test documentation complete

### Final Verification
- [ ] All tests passing locally
- [ ] All tests passing in CI
- [ ] Coverage reports generated
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks established
- [ ] Team trained on running tests

---

## 📊 Success Metrics

### Coverage Targets
- Backend unit tests: 70%+ ✅
- Backend integration tests: 60%+ ✅
- Frontend tests: 60%+ ✅
- E2E critical paths: 100% ✅
- Overall coverage: 65%+ ✅

### Performance Targets
- API response time p95: < 500ms ✅
- Registration endpoint: 100 req/s ✅
- Error rate: < 1% ✅
- Database queries: < 100ms ✅

### Security Targets
- No critical vulnerabilities ✅
- No high vulnerabilities ✅
- All inputs validated ✅
- SQL injection protected ✅
- XSS protected ✅

---

## 🎓 Training & Handoff

### Developer Training (2 hours)
1. Running tests locally
2. Writing new tests
3. Debugging test failures
4. Understanding coverage reports

### CI/CD Training (1 hour)
1. Understanding pipeline
2. Viewing test results
3. Handling failures
4. Deployment gates

### Documentation Handoff
- [ ] TESTING.md reviewed
- [ ] QA_STRATEGY.md reviewed
- [ ] Test examples demonstrated
- [ ] Questions answered

---

## 🚀 Next Steps After Implementation

1. **Monitor test health**
   - Track flaky tests
   - Fix failing tests immediately
   - Maintain coverage above 65%

2. **Expand coverage**
   - Add more edge cases
   - Test error scenarios
   - Add visual regression tests

3. **Performance monitoring**
   - Run load tests weekly
   - Track performance trends
   - Set up alerts for degradation

4. **Security scanning**
   - Run Snyk weekly
   - Update dependencies monthly
   - Review security reports

5. **Continuous improvement**
   - Review test failures
   - Refactor slow tests
   - Update test data
   - Improve test documentation

---

## 📞 Support

**Questions?** Contact QA team or refer to:
- QA_STRATEGY.md - Overall strategy
- TESTING.md - Running tests
- CI/CD logs - Pipeline issues
- Team Slack channel - Quick help

---

**Status:** Ready for implementation
**Estimated Effort:** 80 hours over 2 weeks
**Expected Outcome:** 80%+ test coverage, production-ready quality

Good luck! 🚀
