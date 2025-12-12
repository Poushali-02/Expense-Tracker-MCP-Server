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

# tool 4
@mcp.tool
def get_selected_expenses(start_date:str, end_date:str):
    """
    Docstring for get_selected_expenses
    
    :param start_date: starting day
    :param end_date: ending day
    
    Returns the expenses from these days
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
                "Date": row[3]
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
       
# tool 5
@mcp.tool
def get_summary(start_date:Optional[str] = None, end_date:Optional[str] = None, category:Optional[str] = None):
    """
    Docstring for get_summary
    
    :param start_date: Starting date
    :type start_date: Optional[str]
    :param end_date: Ending date
    :type end_date: Optional[str]
    """
    
    db_connection = get_db()
    db_cursor = db_connection.cursor()
    
    try:
        # based on dates 
        if start_date and end_date and not category:
            params = [start_date, end_date]
            query = f"SELECT * FROM expenses WHERE expense_date BETWEEN %s AND %s GROUP BY category ORDER BY category"
            db_cursor.execute(query, params)
            db_expenses = db_cursor.fetchall()
            expenses = []
            for row in db_expenses:
                expense = {
                    "Expense Id": row[0],
                    "Amount": row[1],
                    "Category": row[2],
                    "Date": row[3]
                }
                expenses.append(expense)
            if expenses:
                return {"result":{
                    "status": "success", 
                    "expenses":expenses,
                    "message": "Expenses tracked on each category"
                }}
            else:
                return {"result":{
                    "status": "success", 
                    "message": "No expense in given dates"
                }}
                
        # based on only category
        elif category and not start_date and not end_date:
            query = f"SELECT * FROM expenses WHERE category = %s"
            db_cursor.execute(query, [category.lower()])
            db_expenses = db_cursor.fetchall()
            expenses = []
            for row in db_expenses:
                expense = {
                    "Expense Id": row[0],
                    "Amount": row[1],
                    "Category": row[2],
                    "Date": row[3]
                }
                expenses.append(expense)
            if expenses:
                return {"result":{
                    "status": "success", 
                    "expenses":expenses,
                    "message": "Expenses tracked on given category"
                }}
            else:
                return {"result":{
                    "status": "success", 
                    "message": "No expense in given category"
                }}
        # all the parameters exist:
        elif start_date and end_date and category:
            params = [start_date, end_date, category.lower()]
            query = f"SELECT * FROM expenses WHERE expense_date BETWEEN %s AND %s AND category=%s"
            db_cursor.execute(query, params)
            db_expenses = db_cursor.fetchall()
            expenses = []
            for row in db_expenses:
                expense = {
                    "Expense Id": row[0],
                    "Amount": row[1],
                    "Category": row[2],
                    "Date": row[3]
                }
                expenses.append(expense)
            if expenses:
                return {"result":{
                    "status": "success", 
                    "expenses":expenses,
                    "message": "Expenses tracked on each category on given dates"
                }}
            else:
                return {"result":{
                    "status": "success", 
                    "message": "No expense in given dates or category"
                }}
    except Exception as e:
        return {"result":{"status": "error", "message": str(e)}}
    
    finally:
        db_cursor.close()
        db_connection.close()

# tool 6
@mcp.tool
def delete_expense(expense_id:str):
    """
    Docstring for delete_expense
    
    :param expense_id: the selected expense will be deleted
    :type expense_id: str
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

# tool 7
@mcp.tool
def get_total_expense(start_date:Optional[str]=None, end_date:Optional[str]=None, category:Optional[str] = None):
    """
    Docstring for get_total_expense
    
    :param start_date: From this date
    :type start_date: Optional[str]
    :param end_date: Upto this date
    :type end_date: Optional[str]
    :param category: On this purpose
    :type categry: Optional[str]
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


# resource 1
CATEGORIES_PATH = Path(__file__).parent / 'Resources' / 'categories.json'
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, 'r') as f:
        categories = json.load(f)
        return categories