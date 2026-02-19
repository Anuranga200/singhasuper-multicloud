import express from 'express';
import { body } from 'express-validator';
import { login, refreshToken } from '../controllers/adminController.js';
import { validate } from '../middleware/validator.js';

const router = express.Router();

// POST /api/admin/login
router.post('/login', [
  body('email').isEmail().withMessage('Valid email is required'),
  body('password').notEmpty().withMessage('Password is required'),
  validate
], login);

// POST /api/admin/refresh
router.post('/refresh', [
  body('refreshToken').notEmpty().withMessage('Refresh token is required'),
  validate
], refreshToken);

export default router;
