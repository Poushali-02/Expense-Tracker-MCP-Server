from fastmcp import FastMCP
from typing import Optional, List
from Database.database import AsyncDatabase
import json
from contextlib import asynccontextmanager
from Tools.AuthenticationTools import auth_tools
from Tools.TransactionTools import reports
from Tools.TransactionTools import changes

@asynccontextmanager
async def lifespan(app):
    # Pre-warm: Initialize DB pool before server accepts requests
    await AsyncDatabase.init_pool()
    yield
    # Cleanup
    await AsyncDatabase.close_pool()

# Create a server instance
mcp = FastMCP(name="Transaction Tracker MCP Server", lifespan=lifespan)

""" ----- Authentication Tools ----- """ 
# Tool 1: Register user
@mcp.tool
async def register_user(
    username:str,
    email:str,
    password:str,
    full_name:str
 ):

    """Register a new user account.
        
        Creates a new user with username, email, and password. Password is hashed
        for security. Returns JWT token on successful registration.
        
        Args:
            username (str): Unique username (required)
            email (str): Valid email address (required)
            password (str): Password with minimum 8 chars, uppercase, lowercase, digit (required)
        
        Returns:
            dict: User ID, token, and success status
    """
    return await auth_tools.register_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name
    )
    
    
# Tool 2: Login user
@mcp.tool
async def login_user(
    username:str,
    password:str
):
    """Authenticate user and get JWT token.
    
    Verifies username and password. Returns JWT token on successful login.
    Token is valid for 24 hours.
    
    Args:
        username (str): Username (required)
        password (str): Password (required)
    
    Returns:
        dict: User ID, token, and success status"""
        
    return await auth_tools.login_user(
        username=username,
        password=password
    )
    
    
# Tool 3: Verify token
@mcp.tool
def verify_token(
    token:str
):
    """Verify JWT token validity.
    
    Checks if token is valid and not expired.
    
    Args:
        token (str): JWT token to verify (required)
    
    Returns:
        dict: Token validity and user info
    """
    return auth_tools.verify_token(token)


# Tool 4: Change password
@mcp.tool
async def change_password(
    user_id:str,
    old_password:str,
    new_password:str
):
    """Change user password.
    
    Updates password after verifying old password. Requires valid user_id.
    
    Args:
        user_id (str): User ID (required)
        old_password (str): Current password (required)
        new_password (str): New password meeting security requirements (required)
    
    Returns:
        dict: Success or error status"""
        
    return await auth_tools.change_password(
        user_id=user_id,
        old_password=old_password,
        new_password=new_password
    )
    
    
# Tool 5: Send Verification Code
@mcp.tool
async def send_verification_code(token: str):
    """Send 6-digit verification code to user's email
    
    Args:
        token(str): JWT Authentication token
        
    Returns:
        dict: Status of email sending
    """
    return await auth_tools.send_verification_code(token=token)


# Tool 6 : Verify Email
@mcp.tool
async def verify_email(code: str):
    """Verify user email with 6-digit code from email.
    
    Args:
        code (str): 6-digit verification code from email
        
    Returns:
        dict: Verification status
    """
    return await auth_tools.verify_email(code=code)


# Tool 7 : Forgot password (Request reset code)
@mcp.tool
async def forgot_password(email:str):
    """Send 6-digit password reset code to email
    
    Args:
        email(str): User's registered email address
    
    Returns:
        dict: Status of reset code sending 
    """    
    return await auth_tools.forgot_password(email=email)

# Tool 8 : Reset password
@mcp.tool
async def reset_password(code:str, new_password:str):
    """Reset password using 6-digit code from email
    
    Args:
        code(str): 6-digit code from password reset email
        new_password (str): New password (min 8 chars, uppercase, lowercase, digit)
        
    Returns:
        dict: Password reset status
    """
    return await auth_tools.reset_password(
        code=code,
        new_password=new_password
    )

""" ----- Transaction Tools -----"""
# Tool 1: add a transactions to the database
@mcp.tool
async def add_transaction(
    token: str,
    amount: float,
    category: str,
    tags: str,
    payment_method: str,
    status: str,
    transaction_type: str,
    *,
    frequency: Optional[str] = None,
    transaction_date: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[str] = None
 ):
    """Add a new expense (debit) to the database.
    
    Creates a new expense record with required and optional fields. Generates a unique
    transaction ID and automatically sets creation timestamp.
    
    Args:
        token (str): Valid JWT token (required)
        amount (float): Expense amount in currency (required)
        category (str): Expense category/type (required)
        tags (str): Tags for expense classification (required)
        payment_method (str): Payment method used (required)
        status (str): Expense status (required)
        frequency (str, optional): Recurrence frequency (daily, weekly, monthly, none, yearly)
        transaction_date (str, optional): Date in YYYY-MM-DD format. Defaults to current date
        notes (str, optional): Additional notes or description
    
    Returns:
        dict: {"result": {"status": "success", "message": "Expense added successfully"}}
    """
    return await changes.add_transaction(
        token=token,
        amount=amount,
        category=category,
        tags=tags,
        payment_method=payment_method,
        status=status,
        transaction_type=transaction_type,
        frequency=frequency,
        transaction_date=transaction_date,
        notes=notes,
        user_id=user_id
    )


# Tool 2: Bulk add transactions
@mcp.tool
async def bulk_add_transactions(
    token: str,
    transactions: List[dict]
):
    """
    Add multiple transactions at once.
    
    Args:
        token (str): JWT authentication token
        transactions (List[dict]): List of transaction objects, each containing:
            - amount (float): Required
            - category (str): Required
            - tags (str): Required
            - payment_method (str): Required
            - status (str): Required
            - transaction_type (str): Required ('expense' or 'credit')
            - frequency (str, optional): 'none', 'daily', 'weekly', 'monthly', 'yearly'
            - transaction_date (str, optional): 'YYYY-MM-DD' format
            - notes (str, optional)
    
    Returns:
        dict: Summary of added transactions with success/failure counts
    """
    return await changes.bulk_add_transactions(
        token=token,
        transactions=transactions
    )
    
    
# Tool 3: get all transactions from db
@mcp.tool
async def get_all_transactions(
    token: str,
    user_id: Optional[str] = None
    ):
    """Retrieve all transactions for authenticated user from the database.
    
    Fetches all transaction records sorted by date in descending order (newest first).
    Returns complete details for each transactions including amount, category, date,
    tags, notes, payment method, status, and frequency.
    
    Returns:
        dict: Transactions list with status and message
    """
    return await reports.get_all_transactions(
        token=token,
        user_id=user_id
    )


# Tool 3: get date wise transactions
@mcp.tool
async def get_selected_transactions(
    token: str,
    start_date: str, 
    end_date: str,
    user_id: Optional[str] = None
    ):
    """Get all transactions within a specified date range.
    
    Retrieves transactions between start_date and end_date (inclusive). Useful for
    viewing transactions for specific time periods. Results are sorted by date in
    descending order.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format (required)
        end_date (str): End date in YYYY-MM-DD format (required)
    
    Returns:
        dict: Transactions list in date range with status and message
    """
    return await reports.get_selected_transactions(
        token=token,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    
# Tool 4: get total expense
@mcp.tool
async def get_total_transactions(
    token: str,
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    category: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Calculate total transactions amount with optional filters.
    
    Sums up all transactions amounts based on provided filters. Useful for understanding
    total transactions in a date range or by category.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        category (str, optional): Filter by specific category
    
    Returns:
        dict: Total amount with status and message
    """
    
    return await reports.get_total_transactions(
        token=token,
        start_date=start_date,
        end_date=end_date,
        category=category,
        user_id=user_id
    )
    
    
# Tool 5: get top category transactions
@mcp.tool
async def get_top_transaction_categories(
    token: str,
    user_id: Optional[str] = None
):
    """Get the top 5 transactions by amount.
    
    Retrieves the 5 highest individual transactions (excluding credits) from the database,
    sorted by amount in descending order. Useful for identifying major expense items.
    
    Returns:
        dict: List of top 5 transactions with details
    """
    return await reports.get_top_transaction_categories(
        token=token,
        user_id=user_id
    )


# Tool 6: get summary of transactions
@mcp.tool
async def get_summary(
    token: str,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Get detailed summary with advanced analytics.
    
    Provides comprehensive analysis with multiple filter options. Returns
    individual transactions plus summary statistics including total, count, average,
    and breakdown by category. Works with any combination of filters.
    
    Args:
        transaction_type (str, optional): 'expense' or 'credit'. None returns both
        category (str, optional): Filter by category
        tags (str, optional): Filter by tags
        payment_method (str, optional): Filter by payment method
        status (str, optional): Filter by status (pending, completed, cancelled)
        frequency (str, optional): Filter by recurrence frequency
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    
    Returns:
        dict: Transactions list with summary statistics (total, count, average, category breakdown)
    """
    return await reports.get_summary(
        token=token,
        transaction_type=transaction_type,
        category=category,
        tags=tags,
        payment_method=payment_method,
        status=status,
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    
# Tool 7: update a single transaction
@mcp.tool
async def update_transaction(
    token: str,
    transaction_id: str,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    transaction_date: Optional[str] = None,
    notes: Optional[str] = None,
    transaction_type: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Update an existing expense record.
    
    Allows partial updates - only provide fields you want to modify. Automatically
    updates the 'updated_at' timestamp. All other fields remain unchanged.
    
    Args:
        transaction_id (str): UUID of the transaction to update (required)
        amount (float, optional): Updated expense amount
        category (str, optional): Updated category
        tags (str, optional): Updated tags
        payment_method (str, optional): Updated payment method
        status (str, optional): Updated status
        frequency (str, optional): Updated recurrence frequency
        transaction_date (str, optional): Updated date in YYYY-MM-DD format
        notes (str, optional): Updated notes/description
    
    Returns:
        dict: Success or error message with status
    """
    return await changes.update_transaction(
        token=token,
        transaction_id=transaction_id,
        amount=amount,
        category=category,
        tags=tags,
        payment_method=payment_method,
        status=status,
        frequency=frequency,
        transaction_date=transaction_date,
        notes=notes,
        transaction_type=transaction_type,
        user_id=user_id
    )
    
    
# Tool 8: Bulk update transactions
@mcp.tool
async def bulk_update_transactions(
    token: str,
    transactions: List[dict],
    user_id: Optional[str] = None
):
    """
    Update multiple transactions at once.
    
    Args:
        token (str): JWT authentication token
        transactions (List[dict]): List of transaction objects, each must contain:
            - transaction_id (str): Required - ID of transaction to update
            - Plus any fields to update: amount, category, tags, payment_method, 
              status, frequency, transaction_date, notes, transaction_type
    
    Returns:
        dict: Summary with success_count, failed_count, and any errors
    """
    return await changes.bulk_update_transactions(
        token=token,
        transactions=transactions,
        user_id=user_id
    )
    
    
# Tool 9: get monthly report
@mcp.tool
async def monthly_report(
    token: str,
    year: int, 
    month: int,
    user_id: Optional[str] = None
):
    """Get monthly transaction report with analytics.
    
    Retrieves all transactions for a specific month and provides detailed analysis
    including total amount, count, average, and category breakdown.
    
    Args:
        year (int): Year in YYYY format (e.g., 2025)
        month (int): Month as number 1-12 (e.g., 12 for December)
    
    Returns:
        dict: transactions list with summary statistics including total, count, average,
              and category breakdown for the specified month
    
    Example:
        monthly_report(year=2025, month=12)
        # Returns all December 2025 transactions with analytics
    """
    return await reports.monthly_report(
        token=token,
        year=year,
        month=month,
        user_id=user_id
    )
    
    
# Tool 10: get balance
@mcp.tool
async def get_balance(
    token: str,
    user_id: Optional[str] = None
):
    """
    Get net balance (total credits - total expenses).
    
    Calculates overall financial balance by subtracting all expenses
    from all credits.
    
    Returns:
        dict: Total credits, total expenses, and net balance
    """
    return await reports.get_balance(
        token=token,
        user_id=user_id
    )
    
# Tool 11: delete a transaction
@mcp.tool
async def delete_transaction(
    token: str,
    transaction_id: str,
    user_id: Optional[str] = None
):
    """Delete a transaction from the database.
    
    Permanently removes a transaction record. Requires valid transaction UUID.
    This operation cannot be undone.
    
    Args:
        transaction_id (str): UUID of the transaction to delete (required)
    
    Returns:
        dict: Status and message confirming deletion or error
    """
    return await changes.delete_transaction(
        token=token,
        transaction_id=transaction_id,
        user_id=user_id
    )
    
    
# Tool 12: delete bulk
@mcp.tool
async def bulk_delete_transaction(
    token:str,
    transaction_ids:List[str],
    user_id:Optional[str] = None
):
    """
    Delete multiple transactions at once.
    
    Args:
        token (str): JWT authentication token
        transaction_ids (List[str]): List of transaction id as str
    
    Returns:
        dict: Summary of deleted transactions with success/failure counts
    
    """
    return await changes.bulk_delete_transactions(
        token=token,
        transaction_ids=transaction_ids,
        user_id=user_id
    )

    
""" ----- Resources -----"""
# Resource 1: categories list
import os
CATEGORIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources', 'categories.json')

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Get available expense categories from configuration file.
    
    Loads and returns the predefined list of expense categories from the
    categories.json resource file. Used for validating and standardizing
    expense categorization across the application.
    
    Returns:
        list/dict: Available expense categories in JSON format
    """
    try:
        with open(CATEGORIES_PATH, 'r') as f:
            categories_data = json.load(f)
            return categories_data
    except FileNotFoundError:
        return {"error": f"categories.json not found at {CATEGORIES_PATH}"}


# Resource Template 2: Get subcategories for a specific category
@mcp.resource("expense://category/{category_name}", mime_type="application/json")
def category_subcategories(category_name: str):
    """Get subcategories/tags for a specific expense category.
    
    Args:
        category_name: Name of the category (e.g., 'food', 'transport', 'health')
    
    Returns:
        list: Available subcategories/tags for the specified category
    """
    try:
        with open(CATEGORIES_PATH, 'r') as f:
            categories_data = json.load(f)
            if category_name.lower() in categories_data:
                return {
                    "category": category_name.lower(),
                    "subcategories": categories_data[category_name.lower()]
                }
            return {"error": f"Category '{category_name}' not found"}
    except FileNotFoundError:
        return {"error": "categories.json not found"}


# Resource Template 3: Get valid payment methods
@mcp.resource("expense://payment-methods", mime_type="application/json")
def payment_methods():
    """Get list of valid payment methods.
    
    Returns:
        list: Available payment methods for transactions
    """
    return {
        "payment_methods": [
            "cash",
            "card",
            "upi",
            "bank",
            "wallet",
            "cheque",
            "other"
        ]
    }


# Resource Template 4: Get valid status options
@mcp.resource("expense://statuses", mime_type="application/json")
def statuses():
    """Get list of valid transaction statuses.
    
    Returns:
        list: Available status options for transactions
    """
    return {
        "statuses": ["pending", "completed", "cancelled"]
    }


# Resource Template 5: Get valid frequency options
@mcp.resource("expense://frequencies", mime_type="application/json")
def frequencies():
    """Get list of valid frequency options for recurring transactions.
    
    Returns:
        list: Available frequency options
    """
    return {
        "frequencies": ["none", "daily", "weekly", "monthly", "yearly"]
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)