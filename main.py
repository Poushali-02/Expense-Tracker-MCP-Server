from fastmcp import FastMCP
from Database.database import get_db
from typing import Optional
from pathlib import Path
import json
from Utilities import utilities

# Create a server instance
mcp = FastMCP(name="Expense Tracker MCP Server")

# tool 1 -> add a transactions to the database
@mcp.tool
def addTransaction(
    amount: float,
    category: str,
    tags: str,
    payment_method: str,
    status: str,
    transaction_type:str,
    frequency: Optional[str] = None,
    transaction_date: Optional[str] = None,
    notes: Optional[str] = None
):
    """Add a new expense (debit) to the database.
    
    Creates a new expense record with required and optional fields. Generates a unique
    transaction ID and automatically sets creation timestamp.
    
    Args:
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
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Normalize inputs
        category = utilities.normalize_category(category)
        
        # Validate inputs
        if not utilities.validate_status(status):
            return {"result": {"status": "error", "message": "Invalid status. Use: pending, completed, cancelled"}}
        
        if not utilities.validate_frequency(frequency):
            return {"result": {"status": "error", "message": "Invalid frequency. Use: none, daily, weekly, monthly, yearly"}}
        
        # Build dynamic query
        params = ['amount', 'transaction_type', 'category', 'tags', 'payment_method', 'status']
        vals = [amount, transaction_type.lower(), category.lower(), tags.lower(), payment_method.lower(), status.lower()]
        
        if frequency:
            params.append('frequency')
            vals.append(frequency.lower())
        
        if transaction_date:
            params.append('transaction_date')
            vals.append(transaction_date)
        
        if notes:
            params.append('notes')
            vals.append(notes.lower())
        
        # Create dynamic query with correct number of placeholders
        placeholders = ', '.join(['%s'] * len(vals))
        query = f"INSERT INTO expenses({', '.join(params)}) VALUES ({placeholders})"
        
        db_cursor.execute(query, vals)
        db_connection.commit()
        
        return {
            "result": {
                "status": "success",
                "message": "Expense added successfully"
            }
        }
        
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 2 -> get all transactions from db
@mcp.tool
def get_all_transactions():
    """Retrieve all transactions from the database.
    
    Fetches all transaction records sorted by date in descending order (newest first).
    Returns complete details for each transactions including amount, category, date,
    tags, notes, payment method, status, and frequency.
    
    Returns:
        dict: Transactions list with status and message
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        transactions = []
        db_cursor.execute(
                """SELECT * FROM expenses ORDER BY transaction_date DESC;"""
            )
        db_transactions = db_cursor.fetchall()
        for row in db_transactions:
            transaction = {
                "Id": str(row[0]),
                "Type": row[1],
                "Date": str(row[2]),
                "Amount": float(row[3]) if row[3] else 0,
                "Category": row[4],
                "Tags": row[5],
                "Notes": row[6],
                "Payment Method": row[7],
                "Status": row[8],
                "Frequency": row[9],
                "Created": str(row[10]),
                "Updated": str(row[11])
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
        db_cursor.close()
        db_connection.close()

# tool 3 -> get date wise transactions
@mcp.tool
def get_selected_transactions(
    start_date:str, 
    end_date:str
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
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build and execute SELECT query
        query = f"SELECT * FROM expenses WHERE transaction_date BETWEEN %s AND %s ORDER BY transaction_date DESC;"
        transactions = []
        date_params = [start_date, end_date]
        db_cursor.execute(query, date_params)
        db_transactions = db_cursor.fetchall()
        for row in db_transactions:
            transaction = {
                "Id": str(row[0]),
                "Type": row[1],
                "Date": str(row[2]),
                "Amount": float(row[3]) if row[3] else 0,
                "Category": row[4],
                "Tags": row[5],
                "Notes": row[6],
                "Payment Method": row[7],
                "Status": row[8],
                "Frequency": row[9],
                "Created": str(row[10]),
                "Updated": str(row[11])
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
        db_cursor.close()
        db_connection.close()
       
# tool 4 -> get total expense
@mcp.tool
def get_total_transactions(
    start_date:Optional[str]=None, 
    end_date:Optional[str]=None, 
    category:Optional[str] = None
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
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        checks = []
        params = []
        if start_date is not None: 
            checks.append(f"transaction_date >= %s")
            params.append(start_date)
            
        if end_date is not None:
            checks.append(f"transaction_date <= %s")
            params.append(end_date)
            
        if category is not None:
            checks.append("category = %s")
            params.append(category.lower())
        
        if not checks:
            return {"result": {"status": "error", "message": "No fields to add"}}
        
        # For Debit
        
        DEBIT_QUERY=f"SELECT * FROM expenses WHERE {' AND '.join(checks)} AND transaction_type='expense' ORDER BY transaction_date DESC"
        db_cursor.execute(DEBIT_QUERY, params)
        db_expenses = db_cursor.fetchall()
        expenses = 0
        for row in db_expenses:
            expenses += row[3]
        
        CREDIT_QUERY=f"SELECT * FROM expenses WHERE {' AND '.join(checks)} AND transaction_type='credit' ORDER BY transaction_date DESC"
        db_cursor.execute(CREDIT_QUERY, params)
        db_credits = db_cursor.fetchall()
        credits = 0
        
        for row in db_credits:
            credits += row[3]
        
        if expenses and credits:
            return {"result":{
                "status": "success", 
                "expense":expenses,
                "credits": credits,
                "Balance": credits - expenses,
                "message": "Total transactions returned successfully"
            }}
        else:
            return {"result":{
                "status": "success", 
                "message": "No expense to return"
            }}

    except Exception as e:
        return {
            "result": {
                "status": "error",
                "message": f"{e}"
            }
        }
    finally:
        db_cursor.close()
        db_connection.close()

# tool 5 -> get top category expenses
@mcp.tool
def get_top_transaction_categories():
    """Get the top 5 expenses by amount.
    
    Retrieves the 5 highest individual expenses (excluding credits) from the database,
    sorted by amount in descending order. Useful for identifying major expense items.
    
    Returns:
        dict: List of top 5 expenses with details
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        categories_credit = []
        categories_debit = []
        
        # Filter for expenses
        DEBIT_QUERY = "SELECT * FROM expenses WHERE transaction_type='expense' ORDER BY amount DESC LIMIT 5"
        db_cursor.execute(DEBIT_QUERY)
        db_expenses = db_cursor.fetchall()
        
        for row in db_expenses:
            if len(row) >= 9:
                expense = {
                    "Id": str(row[0]),
                    "Amount": float(row[1]) if row[1] else 0,
                    "Category": str(row[3]) if len(row) > 3 else "Unknown",
                    "Date": str(row[4]) if len(row) > 4 else "",
                    "Tags": str(row[7]) if len(row) > 7 else "",
                    "Notes": str(row[8]) if len(row) > 8 else "",
                    "Payment Method": str(row[9]) if len(row) > 9 else ""
                }
                categories_debit.append(expense)
        
        
        # Filter for credits
        CREDIT_QUERY = "SELECT * FROM expenses WHERE transaction_type='credit' ORDER BY amount DESC LIMIT 5"
        db_cursor.execute(CREDIT_QUERY)
        db_credits = db_cursor.fetchall()
        
        for row in db_credits:
            if len(row) >= 9:
                credit = {
                    "Id": str(row[0]),
                    "Amount": float(row[1]) if row[1] else 0,
                    "Category": str(row[3]) if len(row) > 3 else "Unknown",
                    "Date": str(row[4]) if len(row) > 4 else "",
                    "Tags": str(row[7]) if len(row) > 7 else "",
                    "Notes": str(row[8]) if len(row) > 8 else "",
                    "Payment Method": str(row[9]) if len(row) > 9 else ""
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
        db_cursor.close()
        db_connection.close()

# tool 6 -> get summary of transactions
@mcp.tool
def get_summary(
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
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
    
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        
        if start_date and end_date:
            where_conditions.append("transaction_date BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        
        if category:
            where_conditions.append("category = %s")
            params.append(category.lower())
        
        if tags:
            where_conditions.append("tags = %s")
            params.append(tags)
        
        if payment_method:
            where_conditions.append("payment_method = %s")
            params.append(payment_method)
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        if frequency:
            where_conditions.append("frequency = %s")
            params.append(frequency)
        
        if transaction_type:
            where_conditions.append("transaction_type = %s")
            params.append(transaction_type)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get all matching transactions
        query = f"SELECT * FROM expenses WHERE {where_clause} ORDER BY transaction_date DESC"
        db_cursor.execute(query, params)
        db_items = db_cursor.fetchall()
        
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
                "Id": str(row[0]),
                "Type": row[1],
                "Date": str(row[2]),
                "Amount": float(row[3]) if row[3] else 0,
                "Category": row[4],
                "Tags": row[5],
                "Notes": row[6],
                "Payment Method": row[7],
                "Status": row[8],
                "Frequency": row[9],
                "Created": str(row[10]),
                "Updated": str(row[11])
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
        db_cursor.close()
        db_connection.close()

# tool 7 -> update a single expense
@mcp.tool
def updateTransaction(
    transaction_id:str,
    amount: Optional[float]=None,
    category: Optional[str]=None,
    tags: Optional[str]=None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    transaction_date: Optional[str] = None,
    notes: Optional[str] = None,
    transaction_type:Optional[str]=None
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
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build dynamic UPDATE query
        updates = []
        params = []
        
        if amount is not None: # amount
            updates.append("amount = %s")
            params.append(amount)
        
        if category is not None: # category
            updates.append("category = %s")
            params.append(category.lower())
        
        if transaction_date is not None: # date
            updates.append("transaction_date = %s")
            params.append(transaction_date)
            
        if tags is not None: # tags
            updates.append("tags = %s")
            params.append(tags.lower())
        
        if payment_method is not None: # payment method
            updates.append("payment_method = %s")
            params.append(payment_method.lower())
        
        if status is not None: # status
            updates.append("status = %s")
            params.append(status.lower())
            
        if frequency is not None: # frequency
            updates.append("frequency = %s")
            params.append(frequency.lower())
        
        if notes is not None: # notes
            updates.append("notes = %s")
            params.append(notes.lower())
        
        if transaction_type is not None: # type
            updates.append("transaction_type = %s")
            params.append(transaction_type.lower())
            
        if not updates:
            return {"result": {"status": "error", "message": "No fields to update"}}
        
        # Add transaction_id as final parameter
        params.append(transaction_id)
        
        # Build and execute UPDATE query
        query = f"UPDATE expenses SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE transaction_id = %s"
        
        db_cursor.execute(query, params)
        db_connection.commit()
        
        if db_cursor.rowcount == 0:
            return {"result": {"status": "error", "message": f"Transaction {transaction_id} not found"}}
        
        return {"result": {"status": "success", "message": "Expense updated successfully"}}
    
    except Exception as e:
        db_connection.rollback()
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 8 -> get monthly report
@mcp.tool
def monthly_report(
    year: int, 
    month: int
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
    
    try:
        # Calculate first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_date = first_day.strftime('%Y-%m-%d')
        end_date = last_day.strftime('%Y-%m-%d')
        month_name = first_day.strftime('%B')
        
        db_connection = get_db()
        db_cursor = db_connection.cursor()
        
        CREDIT_QUERY = """SELECT transaction_id, transaction_type, transaction_date, amount, category, tags, notes, payment_method, status, frequency, created_at, updated_at 
                   FROM expenses WHERE transaction_date >= %s AND transaction_date <= %s 
                   AND transaction_type='credit'
                   ORDER BY transaction_date DESC"""
                   
        DEBIT_QUERY = """SELECT transaction_id, transaction_type, transaction_date, amount, category, tags, notes, payment_method, status, frequency, created_at, updated_at 
                   FROM expenses WHERE transaction_date >= %s AND transaction_date <= %s 
                   AND transaction_type='expense'
                   ORDER BY transaction_date DESC"""
                   
        params = [start_date, end_date]
        
        db_cursor.execute(CREDIT_QUERY, params)
        db_credits = db_cursor.fetchall()
        
        db_cursor.execute(DEBIT_QUERY, params)
        db_expenses = db_cursor.fetchall()
        
        # Separate expenses and credits - removed transaction_type check
        db_expenses = [row for row in db_expenses]
        db_credits = [row for row in db_credits]
        
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
                # Handle dynamic row structure - check available columns
                # Schema order: transaction_id(0), 
                                # transaction_type(1), 
                                # transaction_date(2), 
                                # amount(3), 
                                # category(4), 
                                # tags(5), 
                                # notes(6), 
                                # payment_method(7), 
                                # status(8), 
                                # frequency(9), 
                                # created_at(10), 
                                # updated_at(11)
                expense = {
                    "Id": str(row[0]) if len(row) > 0 else "Unknown",
                    "Type": str(row[1]) if len(row) > 1 else "Unknown",
                    "Date": str(row[2]) if len(row) > 2 else "",
                    "Amount": float(row[3]) if len(row) > 3 and row[3] is not None else 0,
                    "Category": str(row[4]) if len(row) > 4 else "Unknown",
                    "Tags": str(row[5]) if len(row) > 5 else "",
                    "Notes": str(row[6]) if len(row) > 6 else "",
                    "Payment Method": str(row[7]) if len(row) > 7 else "",
                    "Status": str(row[8]) if len(row) > 8 else ""
                }
                expenses.append(expense)
                total_expense += expense["Amount"]
            except (IndexError, TypeError, ValueError) as e:
                continue
            
        for row in db_credits:
            try:
                # Handle dynamic row structure - check available columns
                # Schema order: transaction_id(0), 
                                # transaction_type(1), 
                                # transaction_date(2), 
                                # amount(3), 
                                # category(4), 
                                # tags(5), 
                                # notes(6), 
                                # payment_method(7), 
                                # status(8), 
                                # frequency(9), 
                                # created_at(10), 
                                # updated_at(11)
                credit = {
                    "Id": str(row[0]) if len(row) > 0 else "Unknown",
                    "Type": str(row[1]) if len(row) > 1 else "Unknown",
                    "Date": str(row[2]) if len(row) > 2 else "",
                    "Amount": float(row[3]) if len(row) > 3 and row[3] is not None else 0,
                    "Category": str(row[4]) if len(row) > 4 else "Unknown",
                    "Tags": str(row[5]) if len(row) > 5 else "",
                    "Notes": str(row[6]) if len(row) > 6 else "",
                    "Payment Method": str(row[7]) if len(row) > 7 else "",
                    "Status": str(row[8]) if len(row) > 8 else ""
                }
                credits.append(credit)
                total_credit += credit["Amount"]
            except (IndexError, TypeError, ValueError) as e:
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
        db_cursor.close()
        db_connection.close()
        
# tool 9 -> get balance
@mcp.tool
def balance():
    """
    Get net balance (total credits - total expenses).
    
    Calculates overall financial balance by subtracting all expenses
    from all credits.
    
    Returns:
        dict: Total credits, total expenses, and net balance
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        QUERY=f"SELECT SUM(amount) FROM expenses WHERE transaction_type=%s AND status='completed'"
        
        # for debit
        db_cursor.execute(QUERY, ['expense'])
        expense_result = db_cursor.fetchone()[0]
        expense = float(expense_result) if expense_result else 0
        
        # for credit
        db_cursor.execute(QUERY, ['credit'])
        credit_result = db_cursor.fetchone()[0]
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

# tool 10 -> delete a transaction
@mcp.tool
def delete_transaction(
    transaction_id:str,
    ):
    """Delete a transaction from the database.
    
    Permanently removes a transaction record. Requires valid transaction UUID.
    This operation cannot be undone.
    
    Args:
        transaction_id (str): UUID of the transaction to delete (required)
    
    Returns:
        dict: Status and message confirming deletion or error
    """
    
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        query = f"DELETE FROM expenses WHERE transaction_id=%s"
        db_cursor.execute(query, [transaction_id])
        db_connection.commit()
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
        db_cursor.close()
        db_connection.close()

# resource 1
CATEGORIES_PATH = Path(__file__).parent / 'Resources' / 'categories.json'
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Get available expense categories from configuration file.
    
    Loads and returns the predefined list of expense categories from the
    categories.json resource file. Used for validating and standardizing
    expense categorization across the application.
    
    Returns:
        list/dict: Available expense categories in JSON format
    """
    with open(CATEGORIES_PATH, 'r') as f:
        categories_data = json.load(f)
        return categories_data