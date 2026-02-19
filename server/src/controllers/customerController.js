import pool from '../config/database.js';

/**
 * Validate NIC format (Sri Lankan)
 */
function validateNIC(nic) {
  const oldFormat = /^[0-9]{9}[VvXx]$/;
  const newFormat = /^[0-9]{12}$/;
  return oldFormat.test(nic) || newFormat.test(nic);
}

/**
 * Validate phone number (Sri Lankan)
 */
function validatePhone(phone) {
  const phoneRegex = /^(?:\+94|94|0)?[1-9][0-9]{8}$/;
  return phoneRegex.test(phone);
}

/**
 * Validate name
 */
function validateName(name) {
  const nameRegex = /^[a-zA-Z\s]{2,50}$/;
  return nameRegex.test(name);
}

/**
 * Generate unique 4-digit loyalty number
 */
async function generateLoyaltyNumber() {
  let attempts = 0;
  const maxAttempts = 100;

  while (attempts < maxAttempts) {
    const loyaltyNumber = Math.floor(1000 + Math.random() * 9000).toString();
    
    const [rows] = await pool.query(
      'SELECT id FROM customers WHERE loyalty_number = ?',
      [loyaltyNumber]
    );

    if (rows.length === 0) {
      return loyaltyNumber;
    }
    
    attempts++;
  }

  throw new Error('Unable to generate unique loyalty number');
}

/**
 * Register Customer
 * POST /api/customers/register
 */
export async function registerCustomer(req, res, next) {
  const connection = await pool.getConnection();
  
  try {
    const { nicNumber, fullName, phoneNumber } = req.body;

    // Validate inputs
    if (!validateNIC(nicNumber)) {
      return res.status(400).json({ error: 'Invalid NIC format' });
    }

    if (!validatePhone(phoneNumber)) {
      return res.status(400).json({ error: 'Invalid phone number format' });
    }

    if (!validateName(fullName)) {
      return res.status(400).json({ error: 'Invalid name format' });
    }

    // Sanitize inputs
    const sanitizedNIC = nicNumber.trim().toUpperCase();
    const sanitizedName = fullName.trim();
    const sanitizedPhone = phoneNumber.trim();

    await connection.beginTransaction();

    // Check for duplicate NIC
    const [nicCheck] = await connection.query(
      'SELECT id FROM customers WHERE nic_number = ? AND is_deleted = 0',
      [sanitizedNIC]
    );

    if (nicCheck.length > 0) {
      await connection.rollback();
      return res.status(400).json({ error: 'This NIC number is already registered.' });
    }

    // Check for duplicate phone
    const [phoneCheck] = await connection.query(
      'SELECT id FROM customers WHERE phone_number = ? AND is_deleted = 0',
      [sanitizedPhone]
    );

    if (phoneCheck.length > 0) {
      await connection.rollback();
      return res.status(400).json({ error: 'This phone number is already registered.' });
    }

    // Generate unique loyalty number
    const loyaltyNumber = await generateLoyaltyNumber();

    // Insert customer
    const [result] = await connection.query(
      `INSERT INTO customers (nic_number, full_name, phone_number, loyalty_number, registered_at) 
       VALUES (?, ?, ?, ?, NOW())`,
      [sanitizedNIC, sanitizedName, sanitizedPhone, loyaltyNumber]
    );

    await connection.commit();

    res.json({
      success: true,
      loyaltyNumber: loyaltyNumber
    });
  } catch (error) {
    await connection.rollback();
    next(error);
  } finally {
    connection.release();
  }
}

/**
 * Fetch All Customers
 * GET /api/customers
 */
export async function fetchCustomers(req, res, next) {
  try {
    const [rows] = await pool.query(
      `SELECT id, nic_number, full_name, phone_number, loyalty_number, 
              registered_at, is_deleted 
       FROM customers 
       WHERE is_deleted = 0 
       ORDER BY registered_at DESC`
    );

    // Convert snake_case to camelCase for frontend
    const customers = rows.map(row => ({
      id: row.id.toString(),
      nicNumber: row.nic_number,
      fullName: row.full_name,
      phoneNumber: row.phone_number,
      loyaltyNumber: row.loyalty_number,
      registeredAt: row.registered_at,
      isDeleted: row.is_deleted === 1
    }));

    res.json({
      customers,
      count: customers.length
    });
  } catch (error) {
    next(error);
  }
}

/**
 * Soft Delete Customer
 * DELETE /api/customers/:id
 */
export async function deleteCustomer(req, res, next) {
  try {
    const { id } = req.params;
    const adminEmail = req.user.email;

    // Soft delete: set is_deleted flag
    const [result] = await pool.query(
      `UPDATE customers 
       SET is_deleted = 1, deleted_at = NOW(), deleted_by = ? 
       WHERE id = ? AND is_deleted = 0`,
      [adminEmail, id]
    );

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Customer not found or already deleted' });
    }

    res.json({
      success: true,
      message: `Customer ${id} has been soft deleted`
    });
  } catch (error) {
    next(error);
  }
}
