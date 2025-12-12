from fastmcp import FastMCP
from Database.database import get_db
from typing import Optional
import uuid
from pathlib import Path
import json

# Create a server instance
mcp = FastMCP(name="Expense Tracker MCP Server")

# tool 1 -> add an expense to the database
@mcp.tool
def add_Expense(
    amount: float,
    category: str,
    tags: str,
    payment_method: str,
    status: str,
    frequency: Optional[str] = None,
    expense_date: Optional[str] = None,
    notes: Optional[str] = None
):
    """Add a new expense to the database.
    
    Creates a new expense record with required and optional fields. Generates a unique
    expense ID and automatically sets creation timestamp.
    
    Args:
        amount (float): Expense amount in currency (required)
        category (str): Expense category/type (required)
        tags (str): Tags for expense classification (required)
        payment_method (str): Payment method used (required)
        status (str): Expense status (required)
        frequency (str, optional): Recurrence frequency (daily, weekly, monthly, none)
        expense_date (str, optional): Date in YYYY-MM-DD format. Defaults to current date
        notes (str, optional): Additional notes or description
    
    Returns:
        dict: {"result": {"status": "success", "message": "Expense added successfully"}}
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        expense_id = str(uuid.uuid4())
        
        # Build dynamic query
        params = ['expense_id', 'amount', 'category', 'tags', 'payment_method', 'status']
        vals = [expense_id, amount, category, tags, payment_method, status]
        
        if frequency:
            params.append('frequency')
            vals.append(frequency)
        
        if expense_date:
            params.append('expense_date')
            vals.append(expense_date)
        
        if notes:
            params.append('notes')
            vals.append(notes)
        
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

# tool 2 -> get all expenses from db
@mcp.tool
def get_all_expenses():
    """Retrieve all expenses from the database.
    
    Fetches all expense records sorted by date in descending order (newest first).
    Returns complete details for each expense including amount, category, date,
    tags, notes, payment method, status, and frequency.
    
    Returns:
        dict: Expenses list with status and message
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        expenses = []
        db_cursor.execute(
                """SELECT * FROM expenses ORDER BY expense_date DESC;"""
            )
        db_expenses = db_cursor.fetchall()
        for row in db_expenses:
            expense = {
                "Expense Id": row[0],
                "Amount": row[1],
                "Category": row[2],
                "Date": row[3],
                "Tags": row[6],
                "Notes": row[7],
                "Payment Method": row[8],
                "Status": row[9],
                "Frequency": row[10]
            }
            expenses.append(expense)
        return {"result":{
            "status": "success", 
            "expenses":expenses,
            "message": "Expenses tracked"
        }}
    
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 3 -> update a single expense
@mcp.tool
def updateExpense(
    expense_id:str,
    amount: Optional[float]=None,
    category: Optional[str]=None,
    tags: Optional[str]=None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    expense_date: Optional[str] = None,
    notes: Optional[str] = None
):
    """Update an existing expense record.
    
    Allows partial updates - only provide fields you want to modify. Automatically
    updates the 'updated_at' timestamp. All other fields remain unchanged.
    
    Args:
        expense_id (str): UUID of the expense to update (required)
        amount (float, optional): Updated expense amount
        category (str, optional): Updated category
        tags (str, optional): Updated tags
        payment_method (str, optional): Updated payment method
        status (str, optional): Updated status
        frequency (str, optional): Updated recurrence frequency
        expense_date (str, optional): Updated date in YYYY-MM-DD format
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
            params.append(category)
        
        if expense_date is not None: # date
            updates.append("expense_date = %s")
            params.append(expense_date)
            
        if tags is not None: # tags
            updates.append("tags = %s")
            params.append(tags)
        
        if payment_method is not None: # payment method
            updates.append("payment_method = %s")
            params.append(payment_method)
        
        if status is not None: # status
            updates.append("status = %s")
            params.append(status)
            
        if frequency is not None: # frequency
            updates.append('frequency')
            params.append(frequency)
        
        if notes is not None: # notes
            updates.append('notes')
            params.append(notes)
            
        if not updates:
            return {"result": {"status": "error", "message": "No fields to update"}}
        
        # Add expense_id as final parameter
        params.append(expense_id)
        
        # Build and execute UPDATE query
        query = f"UPDATE expenses SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE expense_id = %s"
        
        db_cursor.execute(query, params)
        db_connection.commit()
        
        if db_cursor.rowcount == 0:
            return {"result": {"status": "error", "message": f"Expense {expense_id} not found"}}
        
        return {"result": {"status": "success", "message": "Expense updated successfully"}}
    
    except Exception as e:
        db_connection.rollback()
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 4 -> get date wise expense
@mcp.tool
def get_selected_expenses(start_date:str, end_date:str):
    """Get all expenses within a specified date range.
    
    Retrieves expenses between start_date and end_date (inclusive). Useful for
    viewing expenses for specific time periods. Results are sorted by date in
    descending order.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format (required)
        end_date (str): End date in YYYY-MM-DD format (required)
    
    Returns:
        dict: Expenses list in date range with status and message
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build and execute UPDATE query
        query = f"SELECT * FROM expenses WHERE expense_date BETWEEN %s AND %s;"
        expenses = []
        date_params = [start_date, end_date]
        db_cursor.execute(query, date_params)
        db_expenses = db_cursor.fetchall()
        for row in db_expenses:
            expense = {
                "Expense Id": row[0],
                "Amount": row[1],
                "Category": row[2],
                "Date": row[3],
                "Tags": row[6],
                "Notes": row[7],
                "Payment Method": row[8],
                "Status": row[9],
                "Frequency": row[10]
            }
            expenses.append(expense)
        if expenses:
            return {"result":{
                "status": "success", 
                "expenses":expenses,
                "message": "Expenses tracked"
            }}
        else:
            return {"result":{
                "status": "success", 
                "message": "No expense in given dates"
            }}
    
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    
    finally:
        db_cursor.close()
        db_connection.close()
       
# tool 5 -> get expense summary
@mcp.tool
def get_summary(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get detailed expense summary with advanced analytics.
    
    Provides comprehensive expense analysis with multiple filter options. Returns
    individual expenses plus summary statistics including total, count, average,
    and breakdown by category. Works with any combination of filters.
    
    Args:
        category (str, optional): Filter by expense category
        tags (str, optional): Filter by tags
        payment_method (str, optional): Filter by payment method
        status (str, optional): Filter by status
        frequency (str, optional): Filter by recurrence frequency
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    
    Returns:
        dict: Expenses list with summary statistics (total, count, average, category breakdown)
    """
    
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        
        if start_date and end_date:
            where_conditions.append("expense_date BETWEEN %s AND %s")
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
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get all matching expenses
        query = f"SELECT * FROM expenses WHERE {where_clause} ORDER BY expense_date DESC"
        db_cursor.execute(query, params)
        db_expenses = db_cursor.fetchall()
        
        if not db_expenses:
            return {"result": {
                "status": "success",
                "message": "No expenses match the given criteria",
                "summary": {
                    "total_amount": 0,
                    "count": 0,
                    "average": 0
                }
            }}
        
        # Process expenses and calculate analytics
        expenses = []
        total_amount = 0
        category_totals = {}
        
        for row in db_expenses:
            expense = {
                "Expense Id": row[0],
                "Amount": float(row[1]),
                "Category": row[2],
                "Date": row[3],
                "Created": row[4],
                "Updated": row[5],
                "Tags": row[6],
                "Notes": row[7],
                "Payment Method": row[8],
                "Status": row[9],
                "Frequency": row[10]
            }
            expenses.append(expense)
            total_amount += expense["Amount"]
            
            # Calculate category totals
            cat = expense["Category"]
            category_totals[cat] = category_totals.get(cat, 0) + expense["Amount"]
        
        # Calculate statistics
        count = len(expenses)
        average = round(total_amount / count, 2) if count > 0 else 0
        
        return {"result": {
            "status": "success",
            "expenses": expenses,
            "summary": {
                "total_amount": round(total_amount, 2),
                "count": count,
                "average": average,
                "category_breakdown": {cat: round(amt, 2) for cat, amt in category_totals.items()}
            },
            "message": f"Found {count} expenses with total amount {total_amount:.2f}Rs"
        }}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 6 -> delete an expense
@mcp.tool
def delete_expense(expense_id:str):
    """Delete an expense from the database.
    
    Permanently removes an expense record. Requires valid expense UUID.
    This operation cannot be undone.
    
    Args:
        expense_id (str): UUID of the expense to delete (required)
    
    Returns:
        dict: Status and message confirming deletion or error
    """
    
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        query = f"DELETE FROM expenses WHERE expense_id=%s"
        db_cursor.execute(query, [expense_id])
        db_connection.commit()
        return {
            "result" : {
                "status": "success",
                "message": "Deleted expense successfully"
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

# tool 7 -> get total expense
@mcp.tool
def get_total_expense(start_date:Optional[str]=None, end_date:Optional[str]=None, category:Optional[str] = None):
    """Calculate total expense amount with optional filters.
    
    Sums up all expense amounts based on provided filters. Useful for understanding
    total spending in a date range or by category.
    
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
            checks.append(f"expense_date >= %s")
            params.append(start_date)
            
        if end_date is not None:
            checks.append(f"expense_date <= %s")
            params.append(end_date)
            
        if category is not None:
            checks.append("category = %s")
            params.append(category.lower())
        
        if not checks:
            return {"result": {"status": "error", "message": "No fields to add"}}
        
        QUERY=f"SELECT * FROM expenses WHERE {' AND '. join(checks)} ORDER BY expense_date DESC"
        db_cursor.execute(QUERY, params)
        db_expenses = db_cursor.fetchall()
        expenses = 0
        for row in db_expenses:
            expenses += row[1]
        if expenses:
            return {"result":{
                "status": "success", 
                "expenses":expenses,
                "message": "Total expense returned successfully"
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

# tool 8 -> get top category expenses
@mcp.tool
def get_top_expense_categories():
    """Get the top 5 expenses by amount.
    
    Retrieves the 5 highest individual expenses from the database, sorted by
    amount in descending order. Useful for identifying major expense items.
    
    Returns:
        dict: List of top 5 expenses with details
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        categories = []
        db_cursor.execute(
                """SELECT * FROM expenses ORDER BY amount DESC;"""
            )
        db_expenses = db_cursor.fetchmany(5)
        for row in db_expenses:
            cats = {
                "Category": row[2],
                "Amount": row[1],
                "Date": row[3],
                "Tags": row[6],
                "Notes": row[7],
                "Payment Method": row[8],
            }
            categories.append(cats)
        return {"result":{
            "status": "success", 
            "expenses":categories,
            "message": "Top 5 expenses tracked"
        }}
    
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 9 -> get monthly report


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