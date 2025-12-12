CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- user table

CREATE TABLE IF NOT EXISTS users(
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(60) UNIQUE NOT NULL,
  full_name VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  active BOOLEAN DEFAULT TRUE
);

-- transactions

CREATE TABLE IF NOT EXISTS transactions (

  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,

  transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  transaction_type VARCHAR(20) DEFAULT 'expense'
    CHECK (transaction_type IN ('expense', 'credit')),
  
  transaction_date DATE DEFAULT CURRENT_DATE,

  amount DECIMAL(20, 2) NOT NULL,
  
  category VARCHAR(60) NOT NULL,
  
  tags TEXT,
  notes TEXT,

  payment_method VARCHAR(50) DEFAULT 'cash',

  status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending', 'completed', 'cancelled')),

  frequency VARCHAR(20) DEFAULT 'none'
    CHECK (frequency IN ('none', 'daily', 'weekly', 'monthly', 'yearly')),
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON transactions(user_id);