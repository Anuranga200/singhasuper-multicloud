# Singha Loyalty System - Backend Server

Express.js REST API server for the Singha Loyalty System, designed to run on AWS ECS Fargate with RDS MySQL.

## Features

- ✅ RESTful API with Express.js
- ✅ MySQL database with connection pooling
- ✅ JWT authentication with refresh tokens
- ✅ Input validation and sanitization
- ✅ CORS and security headers (Helmet)
- ✅ Request compression
- ✅ Health check endpoint
- ✅ Docker containerization
- ✅ Production-ready error handling

## Tech Stack

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Database**: MySQL 8.0 (RDS)
- **Authentication**: JWT (jsonwebtoken)
- **Validation**: express-validator
- **Security**: Helmet, bcryptjs
- **Container**: Docker

## Project Structure

```
server/
├── src/
│   ├── config/
│   │   └── database.js          # MySQL connection pool
│   ├── controllers/
│   │   ├── adminController.js   # Admin login & token refresh
│   │   └── customerController.js # Customer CRUD operations
│   ├── middleware/
│   │   ├── auth.js              # JWT authentication
│   │   ├── validator.js         # Request validation
│   │   └── errorHandler.js      # Global error handler
│   ├── routes/
│   │   ├── admin.js             # Admin routes
│   │   └── customers.js         # Customer routes
│   ├── db/
│   │   ├── schema.sql           # Database schema
│   │   └── migrate.js           # Migration script
│   └── index.js                 # Application entry point
├── Dockerfile                   # Multi-stage Docker build
├── .dockerignore
├── package.json
└── README.md
```

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/customers/register` | Register new customer |

### Protected Endpoints (Require JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/login` | Admin login |
| POST | `/api/admin/refresh` | Refresh access token |
| GET | `/api/customers` | Get all customers |
| DELETE | `/api/customers/:id` | Soft delete customer |

## Local Development

### Prerequisites

- Node.js 18+
- MySQL 8.0
- npm or yarn

### Setup

1. **Install dependencies**
```bash
npm install
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Create database and run migrations**
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE singha_loyalty"

# Run migrations
npm run migrate
```

4. **Start development server**
```bash
npm run dev
```

Server will start on http://localhost:3000

### Testing API

```bash
# Health check
curl http://localhost:3000/health

# Register customer
curl -X POST http://localhost:3000/api/customers/register \
  -H "Content-Type: application/json" \
  -d '{
    "nicNumber": "123456789V",
    "fullName": "John Doe",
    "phoneNumber": "0771234567"
  }'

# Admin login
curl -X POST http://localhost:3000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@singha.com",
    "password": "Admin@123"
  }'

# Get customers (with JWT)
curl http://localhost:3000/api/customers \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## Docker

### Build Image

```bash
docker build -t singha-loyalty-server .
```

### Run Container

```bash
docker run -d \
  -p 3000:3000 \
  -e DB_HOST=your-db-host \
  -e DB_USER=admin \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=singha_loyalty \
  -e JWT_SECRET=your-secret \
  --name singha-server \
  singha-loyalty-server
```

### Docker Compose (Local Development)

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: singha_loyalty
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  server:
    build: .
    ports:
      - "3000:3000"
    environment:
      DB_HOST: mysql
      DB_USER: root
      DB_PASSWORD: rootpassword
      DB_NAME: singha_loyalty
      JWT_SECRET: dev-secret-key
    depends_on:
      - mysql

volumes:
  mysql_data:
```

## Database Schema

### Tables

**admins**
- `id` - Primary key
- `email` - Unique email
- `password_hash` - Bcrypt hashed password
- `full_name` - Admin name
- `is_active` - Active status
- `created_at` - Creation timestamp
- `last_login` - Last login timestamp

**customers**
- `id` - Primary key
- `nic_number` - Unique NIC (Sri Lankan ID)
- `full_name` - Customer name
- `phone_number` - Phone number
- `loyalty_number` - Unique 4-digit loyalty number
- `registered_at` - Registration timestamp
- `is_deleted` - Soft delete flag
- `deleted_at` - Deletion timestamp
- `deleted_by` - Admin who deleted

## Environment Variables

```env
# Server
NODE_ENV=production
PORT=3000
CORS_ORIGIN=*

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your-password
DB_NAME=singha_loyalty

# JWT
JWT_SECRET=your-jwt-secret
JWT_REFRESH_SECRET=your-refresh-secret

# AWS (optional)
AWS_REGION=us-east-1
```

## Security

- Passwords hashed with bcrypt (10 rounds)
- JWT tokens with 1-hour expiration
- Refresh tokens with 7-day expiration
- SQL injection prevention (parameterized queries)
- XSS protection (Helmet middleware)
- CORS configuration
- Input validation and sanitization
- Rate limiting (recommended for production)

## Performance

- Connection pooling (10 connections)
- Response compression (gzip)
- Efficient database queries with indexes
- Health check for load balancer
- Graceful shutdown handling

## Monitoring

### Health Check

```bash
curl http://localhost:3000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-31T10:00:00.000Z",
  "uptime": 3600
}
```

### Logs

Application logs are written to stdout/stderr for CloudWatch integration.

## Production Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for AWS ECS Fargate deployment instructions.

## Troubleshooting

### Database Connection Failed

```bash
# Check MySQL is running
mysql -h <DB_HOST> -u <DB_USER> -p

# Verify credentials in .env
cat .env | grep DB_
```

### Port Already in Use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>
```

### JWT Token Invalid

- Ensure JWT_SECRET matches between environments
- Check token expiration
- Verify Authorization header format: `Bearer <token>`

## License

MIT
