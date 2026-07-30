from app import create_app
from extensions import db
from models import Admin

app = create_app()

with app.app_context():
    admin = Admin.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        admin = Admin(full_name="Administrator", email="admin@gmail.com")
        admin.set_password("admin123")
        db.session.add(admin)
        print("Admin created.")
    else:
        admin.set_password("admin123")
        print("Admin updated.")
    
    db.session.commit()
