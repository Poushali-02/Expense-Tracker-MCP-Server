from fastmcp import FastMCP
from Database.database import get_db, AsyncDatabase
from typing import Optional
from pathlib import Path
import json
from Utilities import utilities
from Utilities.auth import AuthManager
from Utilities.middleware import require_auth
import uuid
from contextlib import asynccontextmanager

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
    db_connection = await get_db()
    
    try:
        isValid, message = await AuthManager.validate_password_strength(password)
        if not isValid:
            return {
                "result": {
                    "status": "error",
                    "message": f"{message}"
                }
            }
            
        # username unique?
        USERNAME_QUERY="SELECT user_id FROM users WHERE username = $1"
        if await db_connection.fetchrow(USERNAME_QUERY, username):
            return {
                "result": {
                    "status": "error",
                    "message": "username already exists"
                }
            }
            
        # email exists?
        EMAIL_QUERY="SELECT user_id FROM users WHERE email = $1"
        if await db_connection.fetchrow(EMAIL_QUERY, email):
            return {
                "result": {
                    "status": "error",
                    "message": "email already exists"
                }
            }
            
        # user id creation
        user_id = str(uuid.uuid4())
        
        # hash password
        password_hash = await AuthManager.hash_password(password)
        EXECUTE_QUERY="""
            INSERT INTO users(user_id, username, full_name, email, password_hash)
            VALUES ($1, $2, $3, $4, $5)
        """
        await db_connection.execute(EXECUTE_QUERY, user_id, username, full_name, email, password_hash)
        
        token = AuthManager.create_token(user_id, username)
        return {"result": {
            "status": "success",
            "user_id": user_id,
            "username": username,
            "token": token,
            "message": "User registered successfully"
        }}
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

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
        
    db_connection = await get_db()
    QUERY="SELECT user_id, password_hash FROM users WHERE username=$1 AND active=TRUE"

    try:
        result = await db_connection.fetchrow(QUERY, username)
        if not result:
            return {
                "result":{
                    "status": "error",
                    "message": "Invalid username or password"
                }
            }
        user_id = str(result['user_id'])
        password_hash = result['password_hash']
        # Verify password
        if not await AuthManager.verify_password(password, password_hash):
            return {"result": {"status": "error", "message": "Invalid username or password"}}
        
        token = AuthManager.create_token(user_id, username)
        return {"result": {
            "status": "success",
            "user_id": user_id,
            "username": username,
            "token": token,
            "message": "Login successful"
        }}
    except Exception as e:
        return {
                "result":{
                    "status": "error",
                    "message": f"{e}"
                }
            }
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

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
    try:
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result":{
                    "status": "error",
                    "message": "Invalid or expired token"
                }
            }
        return {"result": {
            "status": "success",
            "user_id": payload['user_id'],
            "username": payload['username'],
            "message": "Token is valid"
        }}
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}

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
        
    db_connection = await get_db()
    
    try:
        isValid, message = await AuthManager.validate_password_strength(new_password)
        if not isValid:
            return {
                "result":{
                    "status": "error",
                    "message": f"{message}"
                }
            }
        
        # get user
        CHECK_QUERY="SELECT password_hash FROM users WHERE user_id = $1"
        user = await db_connection.fetchrow(CHECK_QUERY, user_id)
        if not user:
            return {
                "result": {
                    "status": "error", 
                    "message": "User not found"
                }
            }
        
        password_hash = user['password_hash']
        
        # verify password
        if not await AuthManager.verify_password(old_password, password_hash):
            return {
                "result": {
                    "status": "error", 
                    "message": "Wrong password"
                }
            }
        
        new_hash = await AuthManager.hash_password(new_password)
        
        ADD_QUERY="UPDATE users SET password_hash=$1, updated_at=CURRENT_TIMESTAMP WHERE user_id=$2"
        await db_connection.execute(ADD_QUERY, new_hash, user_id)
        return {
            "result": {
                "status": "success",
                "message": "Password changed successfully"
            }
        }
           
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)
        
        
""" ----- Transaction Tools -----"""
# Tool 1: add a transactions to the database
@mcp.tool
async def addTransaction(
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
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        # Normalize inputs
        category = utilities.normalize_category(category)
        
        # Validate inputs
        if not utilities.validate_status(status):
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid status. Use: pending, completed, cancelled"
                }
            }
        
        if not utilities.validate_frequency(frequency):
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid frequency. Use: none, daily, weekly, monthly, yearly"
                    
                }
            }
        
        # Build dynamic query with asyncpg placeholders
        params = ['amount', 'transaction_type', 'category', 'tags', 'payment_method', 'status']
        vals = [amount, transaction_type.lower(), category.lower(), tags.lower(), payment_method.lower(), status.lower()]
        
        if frequency:
            params.append('frequency')
            vals.append(frequency.lower())
        
        if transaction_date:
            from datetime import datetime
            params.append('transaction_date')
            # Convert string date (YYYY-MM-DD) to date object
            date_obj = datetime.strptime(transaction_date, '%Y-%m-%d').date()
            vals.append(date_obj)
        
        if notes:
            params.append('notes')
            vals.append(notes.lower())
        
        params.insert(0, 'user_id')
        vals.insert(0, user_id)

        # Create asyncpg placeholders ($1, $2, $3, ...)
        placeholders = ', '.join([f'${i+1}' for i in range(len(vals))])
        query = f"INSERT INTO transactions({', '.join(params)}) VALUES ({placeholders})"
        
        await db_connection.execute(query, *vals)
        
        return {
            "result": {
                "status": "success",
                "message": "Expense added successfully"
            }
        }
        
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

# Tool 2: get all transactions from db
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
    db_connection = await get_db()
    
    try:
        
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        transactions = []
        db_transactions = await db_connection.fetch(
                """SELECT * FROM transactions WHERE user_id=$1 ORDER BY transaction_date DESC;""", user_id
            )
        for row in db_transactions:
            transaction = {
                "Id": str(row['transaction_id']),
                "Type": row['transaction_type'],
                "Date": str(row['transaction_date']),
                "Amount": float(row['amount']) if row['amount'] else 0,
                "Category": str(row['category']),
                "Tags": row['tags'],
                "Notes": row['notes'],
                "Payment Method": row['payment_method'],
                "Status": row['status'],
                "Frequency": row['frequency'],
                "Created": str(row['created_at']),
                "Updated": str(row['updated_at'])
            }
            transactions.append(transaction)
        return {"result":{
            "status": "success", 
            "transactions":transactions,
            "message": "Transactions tracked"
        }}
    
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

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
    db_connection = await get_db()
    
    try:
        
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        # Convert string dates (YYYY-MM-DD) to date objects
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Build and execute SELECT query
        query = f"SELECT * FROM transactions WHERE transaction_date BETWEEN $1 AND $2 AND user_id=$3 ORDER BY transaction_date DESC;"
        transactions = []
        db_transactions = await db_connection.fetch(query, start_date_obj, end_date_obj, user_id)
        for row in db_transactions:
            transaction = {
                "Id": str(row['transaction_id']),
                "Type": row['transaction_type'],
                "Date": str(row['transaction_date']),
                "Amount": float(row['amount']) if row['amount'] else 0,
                "Category": str(row['category']),
                "Tags": row['tags'],
                "Notes": row['notes'],
                "Payment Method": row['payment_method'],
                "Status": row['status'],
                "Frequency": row['frequency'],
                "Created": str(row['created_at']),
                "Updated": str(row['updated_at'])
            }
            transactions.append(transaction)
        if transactions:
            return {"result":{
                "status": "success", 
                "transactions":transactions,
                "message": "Transactions tracked"
            }}
        else:
            return {"result":{
                "status": "success", 
                "message": "No transactions in given dates"
            }}
    
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    
    finally:
        await AsyncDatabase.get_pool().release(db_connection)
       
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
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        checks = []
        params = []
        placeholder_index = 1
        
        # Convert string dates to date objects if provided
        from datetime import datetime
        if start_date is not None: 
            checks.append(f"transaction_date >= ${placeholder_index}")
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            params.append(start_date_obj)
            placeholder_index += 1
            
        if end_date is not None:
            checks.append(f"transaction_date <= ${placeholder_index}")
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            params.append(end_date_obj)
            placeholder_index += 1
            
        if category is not None:
            checks.append(f"category = ${placeholder_index}")
            params.append(category.lower())
            placeholder_index += 1
        
        if not checks:
            return {"result": {"status": "error", "message": "getBalance tool gives the balance with no filters"}}
        
        params.append(user_id)
        user_id_placeholder = placeholder_index
        
        # For Debit
        DEBIT_QUERY = f"SELECT * FROM transactions WHERE {' AND '.join(checks)} AND transaction_type='expense' AND user_id=${user_id_placeholder} ORDER BY transaction_date DESC"
        db_expenses = await db_connection.fetch(DEBIT_QUERY, *params)
        expenses = 0
        for row in db_expenses:
            expenses += float(row['amount']) if row['amount'] else 0
        
        # For credit
        CREDIT_QUERY = f"SELECT * FROM transactions WHERE {' AND '.join(checks)} AND transaction_type='credit' AND user_id=${user_id_placeholder} ORDER BY transaction_date DESC"
        db_credits = await db_connection.fetch(CREDIT_QUERY, *params)
        credits = 0
        
        for row in db_credits:
            credits += float(row['amount']) if row['amount'] else 0
        
        if expenses or credits:
            return {"result":{
                "status": "success", 
                "expense":expenses,
                "credits": credits,
                "Balance": credits - expenses,
                "message": "Total transactions returned successfully"
            }}
        else:
            return {
                "result":{
                    "status": "success", 
                    "message": "No transaction to return"
                }
            }

    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"{e}"
            }
        }
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

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
    db_connection = await get_db()
    
    try:
        
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        categories_credit = []
        categories_debit = []
        
        # Filter for expenses
        DEBIT_QUERY = "SELECT * FROM transactions WHERE transaction_type='expense' AND user_id=$1 ORDER BY amount DESC LIMIT 5"
        db_expenses = await db_connection.fetch(DEBIT_QUERY, user_id)
        
        for row in db_expenses:
            expense = {
                "Id": str(row['transaction_id']),
                "Type": row['transaction_type'],
                "Date": str(row['transaction_date']),
                "Amount": float(row['amount']) if row['amount'] else 0,
                "Category": row['category'],
                "Tags": row['tags'],
                "Notes": row['notes'],
                "Payment Method": row['payment_method'],
                "Status": row['status']
            }
            categories_debit.append(expense)
        
        
        # Filter for credits
        CREDIT_QUERY = "SELECT * FROM transactions WHERE transaction_type='credit' AND user_id=$1 ORDER BY amount DESC LIMIT 5"
        db_credits = await db_connection.fetch(CREDIT_QUERY, user_id)
        
        for row in db_credits:
            credit = {
                "Id": str(row['transaction_id']),
                "Type": row['transaction_type'],
                "Date": str(row['transaction_date']),
                "Amount": float(row['amount']) if row['amount'] else 0,
                "Category": row['category'],
                "Tags": row['tags'],
                "Notes": row['notes'],
                "Payment Method": row['payment_method'],
                "Status": row['status']
            }
            categories_credit.append(credit)
        
        
        return {"result": {
            "status": "success", 
            "expenses": categories_debit,
            "credits": categories_credit,
            "message": f"Top most transactions tracked"
        }}
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

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
    
    db_connection = await get_db()
    
    try:
        
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        placeholder_index = 1
        
        # Convert string dates to date objects if provided
        from datetime import datetime
        if start_date and end_date:
            where_conditions.append(f"transaction_date BETWEEN ${placeholder_index} AND ${placeholder_index + 1}")
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            params.extend([start_date_obj, end_date_obj])
            placeholder_index += 2
        
        if category:
            where_conditions.append(f"category = ${placeholder_index}")
            params.append(category.lower())
            placeholder_index += 1
        
        if tags:
            where_conditions.append(f"tags = ${placeholder_index}")
            params.append(tags)
            placeholder_index += 1
        
        if payment_method:
            where_conditions.append(f"payment_method = ${placeholder_index}")
            params.append(payment_method)
            placeholder_index += 1
        
        if status:
            where_conditions.append(f"status = ${placeholder_index}")
            params.append(status)
            placeholder_index += 1
        
        if frequency:
            where_conditions.append(f"frequency = ${placeholder_index}")
            params.append(frequency)
            placeholder_index += 1
        
        if transaction_type:
            where_conditions.append(f"transaction_type = ${placeholder_index}")
            params.append(transaction_type)
            placeholder_index += 1
        
        where_conditions.append(f"user_id=${placeholder_index}")
        params.append(user_id)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "user_id=$1"
        if not where_conditions:
            params = [user_id]
        
        # Get all matching transactions
        query = f"SELECT * FROM transactions WHERE {where_clause} ORDER BY transaction_date DESC"
        db_items = await db_connection.fetch(query, *params)
        
        if not db_items:
            return {"result": {
                "status": "success",
                "message": "No transactions match the given criteria",
                "summary": {
                    "total_amount": 0,
                    "count": 0,
                    "average": 0,
                    "category_breakdown": {}
                }
            }}
        
        # Process transactions and calculate analytics
        transactions = []
        total_amount = 0
        category_totals = {}
        
        for row in db_items:
            transaction = {
                "Id": str(row['transaction_id']),
                "Type": row['transaction_type'],
                "Date": str(row['transaction_date']),
                "Amount": float(row['amount']) if row['amount'] else 0,
                "Category": str(row['category']),
                "Tags": row['tags'],
                "Notes": row['notes'],
                "Payment Method": row['payment_method'],
                "Status": row['status'],
                "Frequency": row['frequency'],
                "Created": str(row['created_at']),
                "Updated": str(row['updated_at'])
            }
            transactions.append(transaction)
            total_amount += transaction["Amount"]
            
            # Calculate category totals
            cat = transaction["Category"]
            category_totals[cat] = category_totals.get(cat, 0) + transaction["Amount"]
        
        # Calculate statistics
        count = len(transactions)
        average = round(total_amount / count, 2) if count > 0 else 0
        
        return {"result": {
            "status": "success",
            "transactions": transactions,
            "summary": {
                "total_amount": round(total_amount, 2),
                "count": count,
                "average": average,
                "category_breakdown": {cat: round(amt, 2) for cat, amt in category_totals.items()}
            },
            "message": f"Found {count} transactions with total amount Rs {total_amount:.2f}"
        }}
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

# Tool 7: update a single transaction
@mcp.tool
async def updateTransaction(
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
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        # Build dynamic UPDATE query
        updates = []
        params = []
        placeholder_index = 1
        
        if amount is not None:
            updates.append(f"amount = ${placeholder_index}")
            params.append(amount)
            placeholder_index += 1
        
        if category is not None:
            updates.append(f"category = ${placeholder_index}")
            params.append(category.lower())
            placeholder_index += 1
        
        if transaction_date is not None:
            updates.append(f"transaction_date = ${placeholder_index}")
            params.append(transaction_date)
            placeholder_index += 1
            
        if tags is not None:
            updates.append(f"tags = ${placeholder_index}")
            params.append(tags.lower())
            placeholder_index += 1
        
        if payment_method is not None:
            updates.append(f"payment_method = ${placeholder_index}")
            params.append(payment_method.lower())
            placeholder_index += 1
        
        if status is not None:
            updates.append(f"status = ${placeholder_index}")
            params.append(status.lower())
            placeholder_index += 1
            
        if frequency is not None:
            updates.append(f"frequency = ${placeholder_index}")
            params.append(frequency.lower())
            placeholder_index += 1
        
        if notes is not None:
            updates.append(f"notes = ${placeholder_index}")
            params.append(notes.lower())
            placeholder_index += 1
        
        if transaction_type is not None:
            updates.append(f"transaction_type = ${placeholder_index}")
            params.append(transaction_type.lower())
            placeholder_index += 1
            
        if not updates:
            return {"result": {"status": "error", "message": "No fields to update"}}
        
        # Verify transaction exists for this user
        verify_query = "SELECT transaction_id FROM transactions WHERE transaction_id = $1 AND user_id = $2"
        existing = await db_connection.fetchrow(verify_query, transaction_id, user_id)
        if not existing:
            return {"result": {"status": "error", "message": f"Transaction {transaction_id} not found"}}
        
        # Add transaction_id and user_id as final parameters
        params.append(transaction_id)
        params.append(user_id)
        
        # Build and execute UPDATE query
        query = f"UPDATE transactions SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE transaction_id = ${placeholder_index} AND user_id = ${placeholder_index + 1}"
        
        await db_connection.execute(query, *params)
        
        return {"result": {"status": "success", "message": "Expense updated successfully"}}
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

# Tool 8: get monthly report
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
    from datetime import datetime, timedelta
    
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        # Calculate first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Convert to date objects (not strings) for database query
        start_date = first_day.date()
        end_date = last_day.date()
        month_name = first_day.strftime('%B')
        
        CREDIT_QUERY = """SELECT * FROM transactions WHERE transaction_date >= $1 AND transaction_date <= $2 
                   AND transaction_type='credit'
                   AND user_id = $3
                   ORDER BY transaction_date DESC"""
                   
        DEBIT_QUERY = """SELECT * FROM transactions WHERE transaction_date >= $1 AND transaction_date <= $2 
                   AND transaction_type='expense'
                   AND user_id = $3
                   ORDER BY transaction_date DESC"""
                   
        params = [start_date, end_date, user_id]
        
        db_credits = await db_connection.fetch(CREDIT_QUERY, *params)
        db_expenses = await db_connection.fetch(DEBIT_QUERY, *params)
        
        if (not db_credits or len(db_credits) == 0) and (not db_expenses or len(db_expenses) == 0):
            return {"result": {
                "status": "success",
                "month": month_name,
                "year": year,
                "message": f"No transactions found for {month_name} {year}",
                "summary": {
                    "total_expense": 0,
                    "total_credited": 0
                }
            }}
        
        # Process expenses and calculate analytics
        expenses = []
        total_expense = 0
        
        credits = []
        total_credit = 0
        
        for row in db_expenses:
            try:
                expense = {
                    "Id": str(row['transaction_id']),
                    "Type": str(row['transaction_type']),
                    "Date": str(row['transaction_date']),
                    "Amount": float(row['amount']) if row['amount'] is not None else 0,
                    "Category": str(row['category']),
                    "Tags": str(row['tags']) if row['tags'] else "",
                    "Notes": str(row['notes']) if row['notes'] else "",
                    "Payment Method": str(row['payment_method']),
                    "Status": str(row['status'])
                }
                expenses.append(expense)
                total_expense += expense["Amount"]
            except (KeyError, TypeError, ValueError) as e:
                continue
            
        for row in db_credits:
            try:
                credit = {
                    "Id": str(row['transaction_id']),
                    "Type": str(row['transaction_type']),
                    "Date": str(row['transaction_date']),
                    "Amount": float(row['amount']) if row['amount'] is not None else 0,
                    "Category": str(row['category']),
                    "Tags": str(row['tags']) if row['tags'] else "",
                    "Notes": str(row['notes']) if row['notes'] else "",
                    "Payment Method": str(row['payment_method']),
                    "Status": str(row['status'])
                }
                credits.append(credit)
                total_credit += credit["Amount"]
            except (KeyError, TypeError, ValueError) as e:
                continue
        
        if (not expenses or len(expenses) == 0) and (not credits or len(credits) == 0):
            return {"result": {
                "status": "success",
                "month": month_name,
                "year": year,
                "message": f"No transactions found for {month_name} {year}",
                "summary": {
                    "total_expense": 0,
                    "total_credited": 0
                }
            }}
        
        count_exp = len(expenses)
        count_cred = len(credits)
        
        return {"result": {
            "status": "success",
            "month": month_name,
            "year": year,
            "expenses": expenses,
            "credits": credits,
            "summary": {
                "total_expense": round(total_expense, 2),
                "total_credited": round(total_credit, 2)
            },
            "message": f"Monthly report for {month_name} {year}: {count_exp} expenses totaling Rs {total_expense:.2f} and {count_cred} credits totaling Rs {total_credit:.2f}"
        }}
    
    except Exception as e:
        return {"result": {
            "status": "error",
            "message": str(e)
        }}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)
        
# Tool 9: get balance
@mcp.tool
async def getBalance(
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
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        QUERY = "SELECT SUM(amount) FROM transactions WHERE transaction_type=$1 AND status='completed' AND user_id = $2"
        
        # for debit
        expense_result = await db_connection.fetchval(QUERY, 'expense', user_id)
        expense = float(expense_result) if expense_result else 0
        
        # for credit
        credit_result = await db_connection.fetchval(QUERY, 'credit', user_id)
        credit = float(credit_result) if credit_result else 0
        
        total_balance = credit - expense
        return {"result": {
            "status": "success",
            "summary": {
                "total_credits": round(credit, 2),
                "total_expenses": round(expense, 2),
                "net_balance": round(total_balance, 2)
            },
            "message": f"Balance: Rs {total_balance:.2f}"
        }}
        
    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"{e}"
            }
        }
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

# Tool 10: delete a transaction
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
    
    db_connection = await get_db()
    
    try:
        # Authenticate user
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        user_id = payload['user_id']
        
        query = "DELETE FROM transactions WHERE transaction_id=$1 AND user_id=$2"
        await db_connection.execute(query, transaction_id, user_id)
        return {
            "result" : {
                "status": "success",
                "message": "Deleted transaction successfully"
            }
        }
    except Exception as e:
        return {
            "result" : {
                "status": "error",
                "message": f"{e}"
            }
        }
    finally:
        await AsyncDatabase.get_pool().release(db_connection)


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

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)