def transaction_rules():
    return """Transaction Management Rules:

    1. AUTHENTICATION: All transaction operations require a valid JWT token
    2. EMAIL VERIFICATION: User's email must be verified before any transaction operation
    3. OWNERSHIP: Users can only view/edit/delete their own transactions
    4. VALIDATION: 
    - Amount must be positive number
    - Category must be from predefined list (check expense://categories)
    - Status must be: pending, completed, or cancelled
    - Frequency must be: none, daily, weekly, monthly, or yearly
    
    5. BULK OPERATIONS:
    - bulk_add_transactions: Max recommended 50 transactions per call
    - bulk_update_transactions: Each item must include transaction_id
    - bulk_delete_transactions: Provide list of transaction_ids
    
    6. DATE HANDLING:
    - Always use YYYY-MM-DD format
    - If no date provided, current date is used
    
    7. CASE SENSITIVITY:
    - All text fields (category, tags, status) are stored lowercase
    - Input is automatically converted to lowercase

    When user asks to add/update transactions, first check the resources for valid options."""

