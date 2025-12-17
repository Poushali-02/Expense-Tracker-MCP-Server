import asyncpg
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load .env from project root (works regardless of where server is started)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

class AsyncDatabase:
    _pool = None
    
    @classmethod
    async def init_pool(cls):
        """Initialize Connection pool"""
        cls._pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            ssl='require',
            min_size=1,
            max_size=5
        )

    @classmethod
    async def close_pool(cls):
        """Close Connection pool"""
        if cls._pool:
            await cls._pool.close()
    
    @classmethod
    def get_pool(cls):
        """Get the connection pool"""
        return cls._pool
            
    @classmethod
    async def get_connections(cls):
        """Get async database connection"""
        if not cls._pool:
            await cls.init_pool()
        return await cls._pool.acquire()
    
    
async def get_db():
    """Get async database connection"""
    return await AsyncDatabase.get_connections()
