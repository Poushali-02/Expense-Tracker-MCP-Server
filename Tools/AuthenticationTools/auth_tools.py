from Utilities.auth import AuthManager
from Database.database import get_db, AsyncDatabase
import uuid
from Utilities.email_services import EmailService
from Utilities import utilities


"""Register a user"""
async def register_user(
    username:str,
    email:str,
    password:str,
    full_name:str
 ):

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


"""Login a user"""

async def login_user(
    username:str,
    password:str
):  
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


"""Verify token"""
def verify_token(
    token:str
):
    try:
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result":{
                    "status": "error",
                    "message": "Invalid or expired token"
                }
            }
        return {
            "result": {
                "status": "success",
                "user_id": payload['user_id'],
                "username": payload['username'],
                "message": "Token is valid"
            }
        }
    
    except Exception as e:
        return {
            "result": {
                "status": "error", 
                "message": str(e)
            }
        }


"""Change password"""
async def change_password(
    user_id:str,
    old_password:str,
    new_password:str
):      
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
        

"""Send verification mail"""
async def send_verification_code(token: str):
    payload = AuthManager.verify_token(token)
    if not payload:
        return {
            "result": {
                "status":"Error",
                "message": "Invalid or expired token"
            }
        }
        
    user_id = payload['user_id']
    db_connection = await get_db()
    
    try:
        user = await db_connection.fetchrow(
            "SELECT email, username, email_verified FROM users WHERE user_id = $1",
            user_id
        )
        
        if not user:
            return {
            "result": {
                "status":"Error",
                "message": "User not found"
            }
        }
        
        if user['email_verified']:
            return {
            "result": {
                "status":"Info",
                "message": "Email already verified"
            }
        }
            
        verification_code = EmailService.generate_code()
        code_expires = EmailService.get_code_expiry(minutes=5)
        
        await db_connection.execute(
             """UPDATE users 
               SET verification_token = $1, verification_token_expires = $2, verification_attempts = 0 
               WHERE user_id = $3""",
            verification_code, code_expires, user_id
        )
        
        success, message = await EmailService.send_verification_code(
            user['email'], user['username'], verification_code
        )

        if success:
            return {
                "result": {
                    "status": "success",
                    "message": "Verification code sent to your email"
                }
            }
        else:
            return {
                "result": {
                    "status": "Error",
                    "message": message
                }
            }
    
    except Exception as e:
        return {
            "result":{
                "status": "Error",
                "message": str(e)
            }
        }
    
    finally:
        await AsyncDatabase.get_pool().release(db_connection)
      
      
"""Verify Email"""
async def verify_email(code: str):
    MAX_ATTEMPTS = 3
    db_connection = await get_db()
    try:
        user = await db_connection.fetchrow(
            """SELECT user_id, username, verification_token, verification_token_expires, verification_attempts 
               FROM users 
               WHERE verification_token = $1""",
            code
        )
        
        # If code doesn't match, try to find user by checking all active codes and increment their attempts
        if not user:
            # Check if there's a user with pending verification (for attempt tracking)
            return {
                "result": {
                    "status": "Error",
                    "message": "Invalid verification code"
                }
            }
        
        # Check if max attempts exceeded
        if user['verification_attempts'] >= MAX_ATTEMPTS:
            # Invalidate the code
            await db_connection.execute(
                """UPDATE users 
                   SET verification_token = NULL, verification_token_expires = NULL, verification_attempts = 0 
                   WHERE user_id = $1""",
                str(user['user_id'])
            )
            return {
                "result": {
                    "status": "Error",
                    "message": "Too many failed attempts. Please request a new verification code."
                }
            }
        
        from datetime import datetime
        if user['verification_token_expires'] < datetime.utcnow():
            # Clear expired code
            await db_connection.execute(
                """UPDATE users 
                   SET verification_token = NULL, verification_token_expires = NULL, verification_attempts = 0 
                   WHERE user_id = $1""",
                str(user['user_id'])
            )
            return {
                "result":{
                    "status": "Error",
                    "message": "Code expired. Request a new one"
                }
            }
        
        # Success - verify email and clear code
        await db_connection.execute(
            """UPDATE users 
               SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL, verification_attempts = 0 
               WHERE user_id = $1""",
            str(user['user_id'])
        )
        
        return {
            "result":{
                "status": "success",
                "message": "Email verified successfully"
            }
        }
        
    except Exception as e:
        return {
            "result": {
                "status": "Error",
                "message": str(e)
            }
        }
    
    finally:
        await AsyncDatabase.get_pool().release(db_connection)


"""Forgot password request"""
async def forgot_password(email:str):
    db_connection = await get_db()
    
    try:
        user = await db_connection.fetchrow(
            "SELECT user_id, username, email, email_verified FROM users WHERE email = $1",
            email
        )
        
        if not user:
            return {
                "result":{
                    "status": "success",
                    "message": "If this email exists, a reset code has been sent."
                }
            }
            
        # Nothing can act without verifying email
            
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        reset_code = EmailService.generate_code()
        code_expires = EmailService.get_code_expiry(minutes=5)
        
        await db_connection.execute(
            """UPDATE users 
               SET reset_token = $1, reset_token_expires = $2, reset_attempts = 0 
               WHERE user_id = $3""",
            reset_code, code_expires, str(user['user_id'])
        )
        
        success, message = await EmailService.send_password_reset_code(
            user['email'], user['username'], reset_code
        )
        
        if success:
            return {
                "result": {
                    "status": "success", 
                    "message": "Reset code sent to your email"
                }
            }
        else:
            return {
                "result": {
                    "status": "Error", 
                    "message": message
                }
            }
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)


"""Reset password"""
async def reset_password(code:str, new_password:str):
    """Reset password using 6-digit code from email
    
    Args:
        code(str): 6-digit code from password reset email
        new_password (str): New password (min 8 chars, uppercase, lowercase, digit)
        
    Returns:
        dict: Password reset status
    """
    MAX_ATTEMPTS = 3
    db_connection = await get_db()
    
    try:
        isValid, message = await AuthManager.validate_password_strength(new_password)
        if not isValid:
            return {
                "result": {
                    "status": "error", 
                    "message": message
                }
            }
        
        # Find user with this reset code
        user = await db_connection.fetchrow(
            """SELECT user_id, username, reset_token_expires, reset_attempts, email_verified 
               FROM users 
               WHERE reset_token = $1""",
            code
        )
        
        if not user:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid reset code"
                }
            }
        
        # Check if max attempts exceeded
        if user['reset_attempts'] >= MAX_ATTEMPTS:
            # Invalidate the code
            await db_connection.execute(
                """UPDATE users 
                   SET reset_token = NULL, reset_token_expires = NULL, reset_attempts = 0 
                   WHERE user_id = $1""",
                str(user['user_id'])
            )
            return {
                "result": {
                    "status": "error", 
                    "message": "Too many failed attempts. Please request a new reset code."
                }
            }
        
        from datetime import datetime
        if user['reset_token_expires'] < datetime.utcnow():
            # Clear expired code
            await db_connection.execute(
                """UPDATE users 
                   SET reset_token = NULL, reset_token_expires = NULL, reset_attempts = 0 
                   WHERE user_id = $1""",
                str(user['user_id'])
            )
            return {
                "result": {
                    "status": "error", 
                    "message": "Code expired. Please request a new reset code."
                }
            }
            
        # Nothing can act without verifying email
            
        email_verified = utilities.check_email_verified(user)
        if not email_verified:
            return {
                "result":{
                    "status": "Error",
                    "message": "Email address needs to be verified first"
                }
            }
        
        
        new_hash = await AuthManager.hash_password(new_password)
        await db_connection.execute(
            """UPDATE users 
               SET password_hash = $1, reset_token = NULL, reset_token_expires = NULL, reset_attempts = 0 
               WHERE user_id = $2""",
            new_hash, str(user['user_id'])
        )
        
        return {
            "result": {
                "status": "success", 
                "message": f"Password reset successfully for {user['username']}!"
            }
        }
    
    except Exception as e:
        return {"result": {"status": "error", "message": str(e)}}
    finally:
        await AsyncDatabase.get_pool().release(db_connection)

