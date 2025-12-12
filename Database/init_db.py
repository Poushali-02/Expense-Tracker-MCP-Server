from database import get_db

def init_database():
    conn = get_db()
    cur = conn.cursor()
    
    with open('Database/schema.sql', 'r') as f:
        cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database schema initialized!")
    return

if __name__ == "__main__":
    init_database()