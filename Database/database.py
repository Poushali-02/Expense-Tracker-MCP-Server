import psycopg2
import os
from dotenv import load_dotenv
import logging

def get_db():
    # Load environment variables from .env file
    load_dotenv()

    # Database connection details
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = os.getenv("DB_PORT")
    
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        raise ValueError("Missing required database environment variables")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=int(DB_PORT),
            sslmode='disable'
        )

        logging.info("📈 Database Connected")
        return conn
        
    except psycopg2.DatabaseError as e:
        logging.error(f"An error occurred while connecting: {e}")
        raise
