import mysql from 'mysql2/promise';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '.env') });

async function testConnection() {
  console.log('🔍 Testing RDS MySQL Connection...\n');
  console.log('Configuration:');
  console.log(`  Host: ${process.env.DB_HOST}`);
  console.log(`  Port: ${process.env.DB_PORT || 3306}`);
  console.log(`  User: ${process.env.DB_USER}`);
  console.log(`  Database: ${process.env.DB_NAME}\n`);

  let connection;
  
  try {
    // Test connection
    console.log('⏳ Attempting to connect...');
    connection = await mysql.createConnection({
      host: process.env.DB_HOST,
      port: process.env.DB_PORT || 3306,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      connectTimeout: 10000
    });

    console.log('✅ Connection successful!\n');

    // Test query
    console.log('⏳ Running test query...');
    const [rows] = await connection.query('SELECT 1 + 1 AS result, NOW() AS current_time, DATABASE() AS database_name');
    console.log('✅ Query successful!');
    console.log('Result:', rows[0]);
    console.log();

    // Check tables
    console.log('⏳ Checking tables...');
    const [tables] = await connection.query('SHOW TABLES');
    console.log(`✅ Found ${tables.length} tables:`);
    tables.forEach(table => {
      console.log(`  - ${Object.values(table)[0]}`);
    });

  } catch (error) {
    console.error('\n❌ Connection failed!');
    console.error('Error:', error.message);
    console.error('\nCommon issues:');
    console.error('  1. Security group not allowing your IP');
    console.error('  2. RDS instance not publicly accessible');
    console.error('  3. Wrong credentials');
    console.error('  4. Database not created yet');
    process.exit(1);
  } finally {
    if (connection) {
      await connection.end();
      console.log('\n🔌 Connection closed');
    }
  }
}

testConnection();
