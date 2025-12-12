CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS expenses (
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
