from main import app, db
import os

def recreate_database():
    # Ensure the database file is removed if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'social_media.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Existing database file removed.")
        except Exception as e:
            print(f"Error removing existing database: {e}")
            return

    # Create all tables
    with app.app_context():
        try:
            db.create_all()
            print("Database recreated successfully!")
        except Exception as e:
            print(f"Error recreating database: {e}")

if __name__ == '__main__':
    recreate_database() 