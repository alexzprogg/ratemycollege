from app import create_app
from app.models import db, Review  # Make sure Review is imported

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database created successfully.")



