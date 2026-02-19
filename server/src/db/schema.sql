-- Singha Loyalty System Database Schema
-- MySQL 8.0+

-- Create database
CREATE DATABASE IF NOT EXISTS singha_loyalty 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE singha_loyalty;

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP NULL,
  INDEX idx_email (email),
  INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nic_number VARCHAR(20) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  loyalty_number VARCHAR(10) NOT NULL UNIQUE,
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_deleted TINYINT(1) DEFAULT 0,
  deleted_at TIMESTAMP NULL,
  deleted_by VARCHAR(255) NULL,
  UNIQUE KEY uk_nic (nic_number),
  UNIQUE KEY uk_loyalty (loyalty_number),
  INDEX idx_phone (phone_number),
  INDEX idx_deleted (is_deleted),
  INDEX idx_registered (registered_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin (password: Admin@123)
-- Password hash generated with bcrypt (10 rounds)
INSERT INTO admins (email, password_hash, full_name) 
VALUES (
  'admin@singha.com', 
  '$2a$10$rZ5YhkqJxKxKxKxKxKxKxOeH8vKxKxKxKxKxKxKxKxKxKxKxKxKxK',
  'System Administrator'
) ON DUPLICATE KEY UPDATE email=email;

-- Create indexes for performance
CREATE INDEX idx_customer_search ON customers(full_name, nic_number, phone_number);
CREATE INDEX idx_customer_loyalty ON customers(loyalty_number) WHERE is_deleted = 0;
