import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import pool from '../config/database.js';

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || JWT_SECRET;

/**
 * Generate JWT tokens
 */
function generateTokens(email) {
  const accessToken = jwt.sign(
    { email, role: 'admin', userId: 'admin-001' },
    JWT_SECRET,
    { expiresIn: '1h' }
  );

  const refreshToken = jwt.sign(
    { email, role: 'admin', userId: 'admin-001' },
    JWT_REFRESH_SECRET,
    { expiresIn: '7d' }
  );

  return { accessToken, refreshToken };
}

/**
 * Admin Login
 * POST /api/admin/login
 */
export async function login(req, res, next) {
  try {
    const { email, password } = req.body;

    // Fetch admin credentials from database
    const [rows] = await pool.query(
      'SELECT * FROM admins WHERE email = ? AND is_active = 1',
      [email]
    );

    if (rows.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const admin = rows[0];

    // Compare password
    const isValidPassword = await bcrypt.compare(password, admin.password_hash);

    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate tokens
    const { accessToken, refreshToken } = generateTokens(email);

    // Update last login
    await pool.query(
      'UPDATE admins SET last_login = NOW() WHERE id = ?',
      [admin.id]
    );

    res.json({
      success: true,
      token: accessToken,
      refreshToken: refreshToken
    });
  } catch (error) {
    next(error);
  }
}

/**
 * Refresh Token
 * POST /api/admin/refresh
 */
export async function refreshToken(req, res, next) {
  try {
    const { refreshToken } = req.body;

    // Verify refresh token
    let decoded;
    try {
      decoded = jwt.verify(refreshToken, JWT_REFRESH_SECRET);
    } catch (error) {
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }

    // Generate new tokens
    const tokens = generateTokens(decoded.email);

    res.json({
      token: tokens.accessToken,
      refreshToken: tokens.refreshToken
    });
  } catch (error) {
    next(error);
  }
}
