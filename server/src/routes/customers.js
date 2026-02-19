import express from 'express';
import { body } from 'express-validator';
import { 
  registerCustomer, 
  fetchCustomers, 
  deleteCustomer 
} from '../controllers/customerController.js';
import { authenticate } from '../middleware/auth.js';
import { validate } from '../middleware/validator.js';

const router = express.Router();

// POST /api/customers/register (Public)
router.post('/register', [
  body('nicNumber').notEmpty().withMessage('NIC number is required'),
  body('fullName').notEmpty().withMessage('Full name is required'),
  body('phoneNumber').notEmpty().withMessage('Phone number is required'),
  validate
], registerCustomer);

// GET /api/customers (Protected)
router.get('/', authenticate, fetchCustomers);

// DELETE /api/customers/:id (Protected)
router.delete('/:id', authenticate, deleteCustomer);

export default router;
