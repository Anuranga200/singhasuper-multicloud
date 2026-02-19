import bcrypt from 'bcryptjs';
import pool from '../config/database.js';
import dotenv from 'dotenv';

dotenv.config();

/**
 * Database Seeding Script
 * Creates initial admin user and sample data
 */

async function seedDatabase() {
  let connection;
  
  try {
    connection = await pool.getConnection();
    console.log('🌱 Starting database seeding...');

    // 1. Create default admin user
    console.log('Creating admin user...');
    const adminEmail = 'admin@singha.com';
    const adminPassword = 'Admin@123'; // Change in production!
    const passwordHash = await bcrypt.hash(adminPassword, 10);

    await connection.query(`
      INSERT INTO admins (email, password_hash, full_name, is_active)
      VALUES (?, ?, ?, ?)
      ON DUPLICATE KEY UPDATE
        password_hash = VALUES(password_hash),
        full_name = VALUES(full_name)
    `, [adminEmail, passwordHash, 'System Administrator', 1]);

    console.log('✅ Admin user created');
    console.log(`   Email: ${adminEmail}`);
    console.log(`   Password: ${adminPassword}`);

    // 2. Create sample customers (optional)
    console.log('\nCreating sample customers...');
    
    const sampleCustomers = [
      {
        nicNumber: '123456789V',
        fullName: 'John Doe',
        phoneNumber: '0771234567',
        loyaltyNumber: '1001'
      },
      {
        nicNumber: '987654321V',
        fullName: 'Jane Smith',
        phoneNumber: '0779876543',
        loyaltyNumber: '1002'
      },
      {
        nicNumber: '456789123V',
        fullName: 'Bob Johnson',
        phoneNumber: '0774567891',
        loyaltyNumber: '1003'
      }
    ];

    for (const customer of sampleCustomers) {
      await connection.query(`
        INSERT INTO customers (nic_number, full_name, phone_number, loyalty_number)
        VALUES (?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
          full_name = VALUES(full_name),
          phone_number = VALUES(phone_number)
      `, [
        customer.nicNumber,
        customer.fullName,
        customer.phoneNumber,
        customer.loyaltyNumber
      ]);
    }

    console.log(`✅ ${sampleCustomers.length} sample customers created`);

    // 3. Verify data
    const [adminCount] = await connection.query('SELECT COUNT(*) as count FROM admins');
    const [customerCount] = await connection.query('SELECT COUNT(*) as count FROM customers WHERE is_deleted = 0');

    console.log('\n📊 Database Summary:');
    console.log(`   Admins: ${adminCount[0].count}`);
    console.log(`   Customers: ${customerCount[0].count}`);

    console.log('\n✅ Database seeding completed successfully!');
    console.log('\n⚠️  IMPORTANT: Change the default admin password in production!');

  } catch (error) {
    console.error('❌ Seeding failed:', error.message);
    throw error;
  } finally {
    if (connection) {
      connection.release();
    }
    await pool.end();
  }
}

// Run seeding
seedDatabase()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
