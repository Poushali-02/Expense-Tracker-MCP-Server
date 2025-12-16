from typing import Optional
from Database.database import get_db, AsyncDatabase
from Utilities.auth import AuthManager
from Utilities import utilities
from datetime import datetime, timedelta

"""Get all transactions from database"""
async def get_all_transactions(
    token: str,
    user_id: Optional[str] = None
    ):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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
        
        
"""Get filtered transactions datewise"""
async def get_selected_transactions(
    token: str,
    start_date: str, 
    end_date: str,
    user_id: Optional[str] = None
    ):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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
       
       
"""Get total expense"""
async def get_total_transactions(
    token: str,
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    category: Optional[str] = None,
    user_id: Optional[str] = None
):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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


"""Get top transaction categories"""
async def get_top_transaction_categories(
    token: str,
    user_id: Optional[str] = None
):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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
        
        
"""Get comprehensive summary"""
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        # Build WHERE clause dynamically
        
        expected_params = [
            category,
            tags,
            payment_method,
            status,
            frequency,
            transaction_type
        ]
        expected_placeholders = [
            'category',
            'tags',
            'payment_method',
            'status',
            'frequency',
            'transaction_type'
        ]

        where_conditions = []
        params = []
        placeholder_index = 1
        
        for field, param in zip(expected_placeholders, expected_params):
            if param is not None:
                where_conditions.append(f"{field} = ${placeholder_index}")
                params.append(param.lower())
                placeholder_index += 1
        
        # Handle date filters
        if start_date is not None:
            where_conditions.append(f"transaction_date >= ${placeholder_index}")
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            params.append(start_date_obj)
            placeholder_index += 1
            
        if end_date is not None:
            where_conditions.append(f"transaction_date <= ${placeholder_index}")
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            params.append(end_date_obj)
            placeholder_index += 1
        
        # Always add user_id filter
        where_conditions.append(f"user_id = ${placeholder_index}")
        params.append(user_id)
        
        where_clause = " AND ".join(where_conditions)
        
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


"""Get monthly summary"""
async def monthly_report(
    token: str,
    year: int, 
    month: int,
    user_id: Optional[str] = None
):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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
        

"""Get net balance"""
async def get_balance(
    token: str,
    user_id: Optional[str] = None
):
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
            
        # Nothing can act without verifying email
        user = await db_connection.fetchrow(
            "SELECT username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
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
