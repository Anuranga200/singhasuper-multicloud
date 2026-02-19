# Database Migration Best Practices for ECS + RDS

## 🎯 Overview

This guide covers best practices for managing database migrations in a containerized application with RDS in a private subnet.

---

## ✅ Recommended Approach: Container Startup Migrations

**Why this is best:**
- ✅ Automatic - runs every time container starts
- ✅ No manual intervention needed
- ✅ Works with private RDS (no direct access needed)
- ✅ Idempotent - safe to run multiple times
- ✅ Part of deployment pipeline
- ✅ Consistent across environments

**How it works:**
1. Container starts
2. Runs migration script
3. If migration succeeds → starts application
4. If migration fails → container exits (ECS retries)

---

## 📁 Project Structure

```
server/
├── src/
│   ├── db/
│   │   ├── migrate.js          # Migration runner
│   │   ├── schema.sql          # Database schema
│   │   └── seed.js             # Seed data (optional)
│   └── index.js                # Application entry
├── docker-entrypoint.sh        # Startup script
├── Dockerfile                  # Container definition
└── package.json
```

---

## 🔧 Implementation

### 1. Migration Script (`src/db/migrate.js`)

**Key principles:**
- ✅ Use `CREATE TABLE IF NOT EXISTS` (idempotent)
- ✅ Use `INSERT ... ON DUPLICATE KEY UPDATE` (safe)
- ✅ Handle connection errors gracefully
- ✅ Exit with proper error codes
- ✅ Log progress clearly

```javascript
async function migrate() {
  let connection;
  
  try {
    connection = await mysql.createConnection({
      host: process.env.DB_HOST,
      port: process.env.DB_PORT || 3306,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      multipleStatements: true
    });

    console.log('📦 Connected to MySQL server');

    const schema = fs.readFileSync(schemaPath, 'utf8');
    await connection.query(schema);

    console.log('✅ Migration completed successfully');
  } catch (error) {
    console.error('❌ Migration failed:', error.message);
    process.exit(1); // Exit with error code
  } finally {
    if (connection) {
      await connection.end();
    }
  }
}
```

### 2. Schema File (`src/db/schema.sql`)

**Key principles:**
- ✅ Use `IF NOT EXISTS` for all CREATE statements
- ✅ Use proper character sets (utf8mb4)
- ✅ Add indexes for performance
- ✅ Use appropriate data types
- ✅ Add constraints (UNIQUE, NOT NULL)

```sql
-- Always use IF NOT EXISTS
CREATE DATABASE IF NOT EXISTS singha_loyalty 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE singha_loyalty;

-- Idempotent table creation
CREATE TABLE IF NOT EXISTS customers (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nic_number VARCHAR(20) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  loyalty_number VARCHAR(10) NOT NULL UNIQUE,
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_deleted TINYINT(1) DEFAULT 0,
  UNIQUE KEY uk_nic (nic_number),
  INDEX idx_phone (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Safe insert (won't fail if exists)
INSERT INTO admins (email, password_hash, full_name) 
VALUES ('admin@singha.com', '$2a$10$...', 'Admin')
ON DUPLICATE KEY UPDATE email=email;
```

### 3. Docker Entrypoint (`docker-entrypoint.sh`)

**Key principles:**
- ✅ Run migrations before starting app
- ✅ Exit if migration fails
- ✅ Make seeding optional
- ✅ Log each step clearly

```bash
#!/bin/sh
set -e

echo "🚀 Starting application..."

# Run migrations
echo "📦 Running database migrations..."
node src/db/migrate.js

if [ $? -eq 0 ]; then
  echo "✅ Migrations completed"
else
  echo "❌ Migration failed"
  exit 1
fi

# Optional seeding (only for initial setup)
if [ "$RUN_SEED" = "true" ]; then
  echo "🌱 Seeding database..."
  node src/db/seed.js
fi

# Start application
echo "🎯 Starting server..."
exec node src/index.js
```

### 4. Dockerfile

**Key principles:**
- ✅ Copy entrypoint script
- ✅ Make it executable
- ✅ Use it as CMD

```dockerfile
# Copy entrypoint
COPY --chown=nodejs:nodejs docker-entrypoint.sh ./

# Make executable
USER root
RUN chmod +x docker-entrypoint.sh
USER nodejs

# Use entrypoint
CMD ["sh", "docker-entrypoint.sh"]
```

---

## 🚀 Deployment Flow

### First Deployment

```bash
# 1. Build image
docker build -t singha-loyalty:latest .

# 2. Push to ECR
docker push 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest

# 3. Deploy to ECS (with seeding)
# Add environment variable: RUN_SEED=true

# 4. Container starts:
#    → Runs migrations
#    → Creates tables
#    → Seeds data
#    → Starts application
```

### Subsequent Deployments

```bash
# 1. Build and push new image
docker build -t singha-loyalty:latest .
docker push 285229572166.dkr.ecr.us-east-1.amazonaws.com/singha-loyalty:latest

# 2. Update ECS service
# Container starts:
#    → Runs migrations (no changes, idempotent)
#    → Starts application
```

---

## 🔄 Migration Strategies

### Strategy 1: Simple Migrations (Current)

**Best for:**
- Small projects
- Simple schema changes
- Few tables

**Approach:**
- Single `schema.sql` file
- Idempotent statements
- Runs on every startup

**Pros:**
- ✅ Simple
- ✅ Easy to understand
- ✅ No migration tracking needed

**Cons:**
- ❌ Can't rollback
- ❌ Hard to manage complex changes
- ❌ All migrations run every time

### Strategy 2: Versioned Migrations (Recommended for Growth)

**Best for:**
- Growing projects
- Multiple developers
- Complex schema changes

**Approach:**
- Multiple migration files (001_initial.sql, 002_add_column.sql)
- Track applied migrations in database
- Only run new migrations

**Example structure:**
```
src/db/migrations/
├── 001_initial_schema.sql
├── 002_add_loyalty_tiers.sql
├── 003_add_points_table.sql
└── migrate.js (tracks versions)
```

**Implementation:**
```javascript
// Track migrations in database
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INT PRIMARY KEY,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

// Only run new migrations
const appliedMigrations = await getAppliedMigrations();
const pendingMigrations = getAllMigrations().filter(
  m => !appliedMigrations.includes(m.version)
);

for (const migration of pendingMigrations) {
  await runMigration(migration);
  await recordMigration(migration.version);
}
```

### Strategy 3: Migration Tools (Enterprise)

**Best for:**
- Large projects
- Multiple environments
- Team collaboration

**Tools:**
- **Knex.js** - JavaScript migration tool
- **Sequelize** - ORM with migrations
- **Flyway** - Java-based migration tool
- **Liquibase** - Database-independent migrations

**Example with Knex:**
```bash
npm install knex mysql2

# Create migration
npx knex migrate:make add_loyalty_tiers

# Run migrations
npx knex migrate:latest

# Rollback
npx knex migrate:rollback
```

---

## 🛡️ Best Practices Summary

### DO ✅

1. **Make migrations idempotent**
   - Use `IF NOT EXISTS`
   - Use `ON DUPLICATE KEY UPDATE`
   - Safe to run multiple times

2. **Run migrations on container startup**
   - Automatic
   - No manual intervention
   - Works with private RDS

3. **Fail fast**
   - Exit with error code if migration fails
   - Don't start app with broken database

4. **Use transactions for complex migrations**
   ```sql
   START TRANSACTION;
   -- Multiple statements
   COMMIT;
   ```

5. **Test migrations locally first**
   ```bash
   docker build -t test .
   docker run --env-file .env test
   ```

6. **Keep migrations in version control**
   - Track all schema changes
   - Review in pull requests

7. **Separate schema from seed data**
   - schema.sql = structure
   - seed.js = initial data

8. **Use proper data types**
   - VARCHAR for strings
   - BIGINT for IDs
   - TIMESTAMP for dates
   - TINYINT(1) for booleans

9. **Add indexes for performance**
   - Primary keys
   - Foreign keys
   - Frequently queried columns

10. **Use environment variables**
    - Never hardcode credentials
    - Use AWS Secrets Manager for production

### DON'T ❌

1. **Don't run migrations manually**
   - Error-prone
   - Inconsistent across environments
   - Requires direct database access

2. **Don't use DROP TABLE in production**
   - Data loss risk
   - Use soft deletes instead

3. **Don't modify old migrations**
   - Create new migrations instead
   - Keep history intact

4. **Don't skip error handling**
   - Always catch and log errors
   - Exit with proper codes

5. **Don't hardcode values**
   - Use environment variables
   - Use configuration files

6. **Don't forget to test rollbacks**
   - Have a backup plan
   - Test in staging first

7. **Don't run destructive operations without backups**
   - Always backup before major changes
   - Use RDS automated backups

8. **Don't use root user in application**
   - Create dedicated database user
   - Grant only necessary permissions

---

## 🔍 Monitoring & Troubleshooting

### Check Migration Status

**View CloudWatch Logs:**
```bash
# AWS Console → CloudWatch → Log Groups → /ecs/singha-loyalty
# Look for:
✅ "Migration completed successfully"
❌ "Migration failed: ..."
```

**Check ECS Task Status:**
```bash
# AWS Console → ECS → Clusters → Tasks
# If task keeps restarting → migration is failing
```

### Common Issues

**Issue 1: Connection Timeout**
```
❌ Migration failed: connect ETIMEDOUT
```
**Solution:**
- Check RDS security group allows ECS security group
- Verify ECS task has network access to RDS
- Check RDS is in same VPC

**Issue 2: Access Denied**
```
❌ Migration failed: Access denied for user
```
**Solution:**
- Verify DB_USER and DB_PASSWORD are correct
- Check user has CREATE, ALTER, INSERT permissions

**Issue 3: Syntax Error**
```
❌ Migration failed: You have an error in your SQL syntax
```
**Solution:**
- Test SQL locally first
- Check MySQL version compatibility
- Validate schema.sql syntax

---

## 📊 Migration Checklist

Before deploying:

- [ ] Test migration locally with Docker
- [ ] Verify schema.sql syntax
- [ ] Check all environment variables are set
- [ ] Ensure migrations are idempotent
- [ ] Test with empty database
- [ ] Test with existing database
- [ ] Review CloudWatch logs after deployment
- [ ] Verify tables were created correctly
- [ ] Test application endpoints
- [ ] Check ECS task is healthy

---

## 🎓 Advanced Topics

### Blue-Green Deployments

For zero-downtime migrations:

1. **Backward-compatible changes first**
   - Add new columns (nullable)
   - Add new tables
   - Add new indexes

2. **Deploy new code**
   - Uses both old and new schema

3. **Forward-only changes**
   - Remove old columns
   - Rename tables
   - Change constraints

### Database Versioning

Track schema version in database:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
  version VARCHAR(20) PRIMARY KEY,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial schema')
ON DUPLICATE KEY UPDATE version=version;
```

### Rollback Strategy

Always have a rollback plan:

```bash
# 1. Backup before migration
aws rds create-db-snapshot \
  --db-instance-identifier singha-loyalty-db \
  --db-snapshot-identifier pre-migration-$(date +%Y%m%d)

# 2. If migration fails, restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier singha-loyalty-db \
  --db-snapshot-identifier pre-migration-20260201
```

---

## 📚 Resources

- [MySQL Best Practices](https://dev.mysql.com/doc/)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

**Summary:** For your project, the current approach (migrations on container startup) is the best practice. It's simple, automatic, and works perfectly with ECS + private RDS. As your project grows, consider moving to versioned migrations.
