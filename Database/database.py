import asyncpg
import os
from dotenv import load_dotenv
import logging

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5433)

class AsyncDatabase:
    _pool = None
    
    @classmethod
    async def init_pool(cls):
        """Initialize Connection pool"""
        cls._pool = await asyncpg.create_pool(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=int(DB_PORT),
            ssl=False,
            min_size=10,
            max_size=20
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
