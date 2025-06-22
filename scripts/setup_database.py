import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.models import Base
from app.database import engine
from app.config import settings
import getpass
from app.models import User
from app.auth import get_password_hash
from app.database import SessionLocal


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")


def create_admin_user():
    print("\nCreating admin user...")
    email = input("Admin email: ")
    password = getpass.getpass("Admin password: ")

    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print("❌ User with this email already exists")
        return

    admin_user = User(
        email=email,
        password_hash=get_password_hash(password),
        role="admin"
    )

    db.add(admin_user)
    db.commit()
    db.close()

    print("✅ Admin user created successfully")


def main():
    print("NSF AI App Database Setup")
    print("=" * 30)

    try:
        create_tables()
        create_admin_user()
        print("\n🎉 Database setup complete!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()