from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE products ADD COLUMN discount_price NUMERIC(10, 2) DEFAULT NULL;"))
        print("Added discount_price")
    except Exception as e:
        print(f"Error adding discount_price: {e}")
        
    try:
        db.session.execute(text("ALTER TABLE products ADD COLUMN offers VARCHAR(255) DEFAULT NULL;"))
        print("Added offers")
    except Exception as e:
        print(f"Error adding offers: {e}")
        
    db.session.commit()
