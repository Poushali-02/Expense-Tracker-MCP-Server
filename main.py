from fastmcp import FastMCP
from Database.database import get_db
from typing import Optional
import uuid

# Create a server instance
mcp = FastMCP(name="Expense Tracker MCP Server")

# tool 1 -> add an expense to the database
@mcp.tool
def add_Expense(
    expense_amount:float, 
    expense_description:str, 
    expense_date:Optional[str]
    ):
    """This tool will add expense to the database directly and return message
    Args: expense amount, expense description, expense date(optional)
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        expense_id = str(uuid.uuid4())
        if expense_date:
            db_cursor.execute(
                """INSERT INTO expenses(expense_id, 
                                    amount, 
                                    category, 
                                    expense_date) 
                VALUES (%s, %s, %s, %s)""",
                (expense_id, expense_amount, expense_description, expense_date)
            )
            db_connection.commit()
            return {"result":{"status": "success", "message":"Expense added successfully"}}
        else:
            db_cursor.execute(
                """INSERT INTO expenses(expense_id, 
                                    amount, 
                                    category) 
                VALUES (%s, %s, %s)""",
                (expense_id, expense_amount, expense_description)
            )
            db_connection.commit()
            return {"result":{"status": "success", "message":"Expense added successfully"}}
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    finally:
        db_cursor.close()
        db_connection.close()

# tool 2
@mcp.tool
def get_all_expenses():
    """This tool will get all expenses from the database directly 
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
                "Date": row[3]
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

# tool 3 
@mcp.tool
def updateExpense(
    expense_id: str,
    expense_amount: Optional[float] = None, 
    expense_description: Optional[str] = None, 
    expense_date: Optional[str] = None
):
    """Update an expense in the database. Only provide fields you want to update
    Args: expense_id (required), and any optional fields to update
    """
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # Build dynamic UPDATE query
        updates = []
        params = []
        
        if expense_amount is not None:
            updates.append("amount = %s")
            params.append(expense_amount)
        
        if expense_description is not None:
            updates.append("category = %s")
            params.append(expense_description)
        
        if expense_date is not None:
            updates.append("expense_date = %s")
            params.append(expense_date)
        
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

