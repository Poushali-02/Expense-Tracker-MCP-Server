# ---- UTILITIES ----

def normalize_category(category: str) -> str:
    """Normalize category names to lowercase for consistency"""
    return category.lower().strip() if category else category

def validate_transaction_type(transaction_type: str) -> bool:
    """Validate transaction type is either expense or credit"""
    return transaction_type in ['expense', 'credit'] if transaction_type else True

def validate_status(status: str) -> bool:
    """Validate status is valid"""
    return status in ['pending', 'completed', 'cancelled'] if status else True

def validate_frequency(frequency: str) -> bool:
    """Validate frequency is valid"""
    return frequency in ['none', 'daily', 'weekly', 'monthly'] if frequency else True

def check_email_verified(user) -> bool:
    return user['email_verified']