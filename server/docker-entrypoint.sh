#!/bin/sh
set -e

echo "🚀 Starting Singha Loyalty Application..."

# Run database migrations (SAFE - won't delete data)
echo "📦 Running database migrations..."
node src/db/migrate.js

# Check if migration was successful
if [ $? -eq 0 ]; then
  echo "✅ Migrations completed successfully"
else
  echo "❌ Migration failed"
  exit 1
fi

# Run database seeding (ONLY if RUN_SEED=true)
# Set this environment variable ONLY on first deployment
if [ "$RUN_SEED" = "true" ]; then
  echo "🌱 Seeding database..."
  echo "⚠️  WARNING: This will update existing sample data"
  node src/db/seed.js
fi

# Start the application
echo "🎯 Starting application server..."
exec node src/index.js
