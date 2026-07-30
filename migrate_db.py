import sqlite3

def upgrade_database():
    conn = sqlite3.connect('instance/app.db')  # Assumes default flask SQLAlchemy location
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN discount_price NUMERIC(10, 2) DEFAULT NULL;")
        print("Added discount_price column successfully.")
    except sqlite3.OperationalError as e:
        print(f"discount_price column might already exist: {e}")

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN offers VARCHAR(255) DEFAULT NULL;")
        print("Added offers column successfully.")
    except sqlite3.OperationalError as e:
        print(f"offers column might already exist: {e}")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    upgrade_database()
