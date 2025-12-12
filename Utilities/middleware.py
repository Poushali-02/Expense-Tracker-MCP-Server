from Utilities.auth import AuthManager
from typing import Optional, Dict
from functools import wraps

def require_auth(func):
    """Decorator to require auth token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # extract token from kwargs
        token = kwargs.pop('token', None)
        if not token:
            return {
                "result": {
                    "status": "error", 
                    "message": "Authentication token required"
                }
            }
            
        # verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            return {
                "result": {
                    "status": "error", 
                    "message": "Invalid or expired token"
                }
            }
        
        # add user_id to kwargs
        kwargs['user_id'] = payload['user_id']
        
        return func(*args, **kwargs)
    
    return wrapper