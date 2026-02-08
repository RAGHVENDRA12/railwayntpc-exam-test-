import models
import database
from passlib.context import CryptContext

# Init DB
database.init_db()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def test_add_user():
    db = database.SessionLocal()
    try:
        username = "debug_user"
        password = "debug_password"
        
        # Check if exists
        if db.query(models.User).filter(models.User.username == username).first():
            print("User already exists")
            return

        new_user = models.User(username=username, hashed_password=get_password_hash(password))
        db.add(new_user)
        db.commit()
        print("User added successfully via script")
    except Exception as e:
        print(f"Error adding user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_add_user()
