import models
import database
from passlib.context import CryptContext
import sys

# Init DB (should already be initialized by server, but this ensures tables exist)
database.init_db()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def test_add_user():
    print("Connecting to DB...")
    db = database.SessionLocal()
    try:
        username = "script_user"
        password = "script_password"
        
        print(f"Checking if {username} exists...")
        if db.query(models.User).filter(models.User.username == username).first():
            print("User already exists")
        else:
            print("Creating new user...")
            new_user = models.User(username=username, hashed_password=get_password_hash(password))
            db.add(new_user)
            print("Committing...")
            db.commit()
            print("User added successfully via script")
            
    except Exception as e:
        print(f"Error adding user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing connection...")
        db.close()

if __name__ == "__main__":
    test_add_user()
