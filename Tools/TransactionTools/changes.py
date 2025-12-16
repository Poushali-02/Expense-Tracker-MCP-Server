from typing import Optional, List
from Database.database import get_db, AsyncDatabase
from Utilities.auth import AuthManager
from Utilities import utilities

expected_updates = [
    'amount',
    'category',
    'transaction_date',
    'tags',
    'payment_method',
    'status',
    'frequency',
    'notes',
    'transaction_type'
]
string_fields = {
    'category', 
    'tags', 
    'payment_method', 
    'status', 
    'frequency', 
    'notes', 
    'transaction_type'
}

# INSERT
"""Add a transaction to database"""
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


"""Bulk add transactions to database"""
async def bulk_add_transactions(
    token: str,
    transactions: List[dict]
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
                "result": {
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        if not transactions or len(transactions) == 0:
            return {
                "result": {
                    "status": "error",
                    "message": "No transactions provided"
                }
            }
        
        success_count = 0
        failed_count = 0
        errors = []
        
        from datetime import datetime
        
        for idx, txn in enumerate(transactions):
            try:
                # Validate required fields
                required = ['amount', 'category', 'tags', 'payment_method', 'status', 'transaction_type']
                missing = [f for f in required if f not in txn or txn[f] is None]
                if missing:
                    errors.append(f"Transaction {idx + 1}: Missing fields: {', '.join(missing)}")
                    failed_count += 1
                    continue
                
                # Validate status
                if not utilities.validate_status(txn['status']):
                    errors.append(f"Transaction {idx + 1}: Invalid status")
                    failed_count += 1
                    continue
                
                # Validate frequency if provided
                frequency = txn.get('frequency')
                if frequency and not utilities.validate_frequency(frequency):
                    errors.append(f"Transaction {idx + 1}: Invalid frequency")
                    failed_count += 1
                    continue
                
                # Build query
                params = ['user_id', 'amount', 'transaction_type', 'category', 'tags', 'payment_method', 'status']
                vals = [
                    user_id,
                    txn['amount'],
                    txn['transaction_type'].lower(),
                    utilities.normalize_category(txn['category']).lower(),
                    txn['tags'].lower(),
                    txn['payment_method'].lower(),
                    txn['status'].lower()
                ]
                
                if frequency:
                    params.append('frequency')
                    vals.append(frequency.lower())
                
                if txn.get('transaction_date'):
                    params.append('transaction_date')
                    date_obj = datetime.strptime(txn['transaction_date'], '%Y-%m-%d').date()
                    vals.append(date_obj)
                
                if txn.get('notes'):
                    params.append('notes')
                    vals.append(txn['notes'].lower())
                
                placeholders = ', '.join([f'${i+1}' for i in range(len(vals))])
                query = f"INSERT INTO transactions({', '.join(params)}) VALUES ({placeholders})"
                
                await db_connection.execute(query, *vals)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Transaction {idx + 1}: {str(e)}")
                failed_count += 1
        
        return {
            "result": {
                "status": "success" if success_count > 0 else "error",
                "message": f"Added {success_count} transactions, {failed_count} failed",
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors if errors else None
            }
        }
        
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)


# UPDATE
"""Update a single transaction"""
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
        
        # Build dynamic UPDATE query
        
        expected_params = [
            amount,
            category,
            transaction_date,
            tags,
            payment_method,
            status,
            frequency,
            notes,
            transaction_type
        ]
        
        updates = []
        params = []
        placeholder_index = 1
        
        for update, param in zip(expected_updates, expected_params):
            if param is not None:
                if update in string_fields and isinstance(param, str):
                    param = param.lower()
                updates.append(f"{update} = ${placeholder_index}")
                params.append(param)
                placeholder_index+=1
                
        if not updates:
            return {
                "result": {
                    "status": "error", 
                    "message": "No fields to update"
                }
            }
        
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


"""Bulk update transactions"""
async def bulk_update_transactions(
    token: str,
    transactions: List[dict],
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
                "result": {
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        if not transactions or len(transactions) == 0:
            return {
                "result": {
                    "status": "error",
                    "message": "No transactions provided"
                }
            }
        
        success_count = 0
        failed_count = 0
        errors = []
        
        from datetime import datetime
        
        string_fields = {'category', 'tags', 'payment_method', 'status', 'frequency', 'notes', 'transaction_type'}
        
        for idx, txn in enumerate(transactions):
            try:
                # transaction_id is required for updates
                if 'transaction_id' not in txn or not txn['transaction_id']:
                    errors.append(f"Transaction {idx + 1}: Missing transaction_id")
                    failed_count += 1
                    continue
                
                transaction_id = txn['transaction_id']
                
                # Verify transaction exists and belongs to user
                existing = await db_connection.fetchrow(
                    "SELECT transaction_id FROM transactions WHERE transaction_id = $1 AND user_id = $2",
                    transaction_id, user_id
                )
                if not existing:
                    errors.append(f"Transaction {idx + 1}: Not found or not owned by user")
                    failed_count += 1
                    continue
                
                # Validate status if provided
                if txn.get('status') and not utilities.validate_status(txn['status']):
                    errors.append(f"Transaction {idx + 1}: Invalid status")
                    failed_count += 1
                    continue
                
                # Validate frequency if provided
                if txn.get('frequency') and not utilities.validate_frequency(txn['frequency']):
                    errors.append(f"Transaction {idx + 1}: Invalid frequency")
                    failed_count += 1
                    continue
                
                # Build dynamic UPDATE query
                update_fields = ['amount', 'category', 'transaction_date', 'tags', 
                                'payment_method', 'status', 'frequency', 'notes', 'transaction_type']
                
                updates = []
                params = []
                placeholder_index = 1
                
                for field in update_fields:
                    if field in txn and txn[field] is not None:
                        value = txn[field]
                        
                        # Handle date conversion
                        if field == 'transaction_date':
                            value = datetime.strptime(value, '%Y-%m-%d').date()
                        # Handle string fields - lowercase
                        elif field in string_fields and isinstance(value, str):
                            value = value.lower()
                        
                        updates.append(f"{field} = ${placeholder_index}")
                        params.append(value)
                        placeholder_index += 1
                
                if not updates:
                    errors.append(f"Transaction {idx + 1}: No fields to update")
                    failed_count += 1
                    continue
                
                # Add transaction_id and user_id as final parameters
                params.append(transaction_id)
                params.append(user_id)
                
                query = f"UPDATE transactions SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE transaction_id = ${placeholder_index} AND user_id = ${placeholder_index + 1}"
                
                await db_connection.execute(query, *params)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Transaction {idx + 1}: {str(e)}")
                failed_count += 1
        
        return {
            "result": {
                "status": "success" if success_count > 0 else "error",
                "message": f"Updated {success_count} transactions, {failed_count} failed",
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors if errors else None
            }
        }
        
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)


# DELETE
"""Delete a transaction from database"""
async def delete_transaction(
    token: str,
    transaction_id: str,
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


"""Bulk delete from database for single user"""
async def bulk_delete_transactions(
    token: str,
    transaction_ids: List[str],
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
                "result": {
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        if not transaction_ids or len(transaction_ids) == 0:
            return {
                "result": {
                    "status": "error",
                    "message": "No transaction IDs provided"
                }
            }
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for idx, txn_id in enumerate(transaction_ids):
            try:
                if not txn_id:
                    errors.append(f"Transaction {idx + 1}: Missing transaction ID")
                    failed_count += 1
                    continue
                
                # Verify transaction exists for this user before deleting
                existing = await db_connection.fetchrow(
                    "SELECT transaction_id FROM transactions WHERE transaction_id = $1 AND user_id = $2",
                    txn_id, user_id
                )
                
                if not existing:
                    errors.append(f"Transaction {idx + 1}: Not found or not owned by user")
                    failed_count += 1
                    continue
                
                # Delete transaction
                query = "DELETE FROM transactions WHERE transaction_id = $1 AND user_id = $2"
                await db_connection.execute(query, txn_id, user_id)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Transaction {idx + 1}: {str(e)}")
                failed_count += 1
        
        return {
            "result": {
                "status": "success" if success_count > 0 else "error",
                "message": f"Deleted {success_count} transactions, {failed_count} failed",
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors if errors else None
            }
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "error", 
                "message": str(e)
            }
        }
    finally:
        await AsyncDatabase.get_pool().release(db_connection)
