CREATE TABLE IF NOT EXISTS expenses (
    expense_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amount DECIMAL(20, 2) NOT NULL,
    category VARCHAR(60) NOT NULL,
    expense_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,
    notes TEXT,
    payment_method VARCHAR(50) DEFAULT 'cash',
    status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'cancelled')),
    frequency VARCHAR(20) DEFAULT 'none' CHECK(frequency IN ('none', 'daily', 'weekly', 'monthly', 'yearly')),
);