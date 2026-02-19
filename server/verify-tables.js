import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

async function verifyTables() {
  let connection;
  
  try {
    console.log('🔍 Connecting to RDS MySQL...');
    console.log(`   Host: ${process.env.DB_HOST}`);
    console.log(`   Database: ${process.env.DB_NAME}`);
    
    // Connect to database
    connection = await mysql.createConnection({
      host: process.env.DB_HOST,
      port: process.env.DB_PORT || 3306,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME
    });

    console.log('✅ Connected successfully\n');

    // Check if database exists
    const [databases] = await connection.query(
      "SHOW DATABASES LIKE 'singha_loyalty'"
    );
    
    if (databases.length === 0) {
      console.log('❌ Database "singha_loyalty" does NOT exist');
      process.exit(1);
    }
    
    console.log('✅ Database "singha_loyalty" exists\n');

    // List all tables
    console.log('📋 Checking tables...\n');
    const [tables] = await connection.query('SHOW TABLES');
    
    if (tables.length === 0) {
      console.log('❌ No tables found in database');
      process.exit(1);
    }

    console.log(`✅ Found ${tables.length} table(s):\n`);
    
    // Check each table
    for (const tableRow of tables) {
      const tableName = Object.values(tableRow)[0];
      console.log(`📊 Table: ${tableName}`);
      
      // Get row count
      const [countResult] = await connection.query(
        `SELECT COUNT(*) as count FROM ${tableName}`
      );
      const rowCount = countResult[0].count;
      
      // Get table structure
      const [columns] = await connection.query(
        `DESCRIBE ${tableName}`
      );
      
      console.log(`   Rows: ${rowCount}`);
      console.log(`   Columns: ${columns.length}`);
      console.log(`   Structure:`);
      
      columns.forEach(col => {
        console.log(`      - ${col.Field} (${col.Type}) ${col.Key ? '[' + col.Key + ']' : ''}`);
      });
      
      console.log('');
    }

    // Verify expected tables exist
    const expectedTables = ['admins', 'customers'];
    const existingTableNames = tables.map(t => Object.values(t)[0]);
    
    console.log('🔍 Verification Summary:\n');
    
    let allTablesExist = true;
    for (const expectedTable of expectedTables) {
      if (existingTableNames.includes(expectedTable)) {
        console.log(`   ✅ ${expectedTable} - EXISTS`);
      } else {
        console.log(`   ❌ ${expectedTable} - MISSING`);
        allTablesExist = false;
      }
    }
    
    console.log('');
    
    if (allTablesExist) {
      console.log('✅ All required tables exist!');
      console.log('🎉 Database is ready for use!');
    } else {
      console.log('❌ Some required tables are missing');
      console.log('💡 Run: npm run migrate');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Verification failed:', error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Check DB_HOST is correct');
      console.log('   - Check RDS security group allows your IP');
      console.log('   - Check RDS is in "Available" state');
    } else if (error.code === 'ER_ACCESS_DENIED_ERROR') {
      console.log('\n💡 Troubleshooting:');
      console.log('   - Check DB_USER is correct');
      console.log('   - Check DB_PASSWORD is correct');
    } else if (error.code === 'ER_BAD_DB_ERROR') {
      console.log('\n💡 Database does not exist');
      console.log('   Run: npm run migrate');
    }
    
    process.exit(1);
  } finally {
    if (connection) {
      await connection.end();
    }
  }
}

verifyTables();
