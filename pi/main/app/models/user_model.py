# app/models/user_model.py
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.connection import get_connection

def find_user_by_email(email):
    db = get_connection()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        return cursor.fetchone()

def create_user(email, password):
    db = get_connection()
    with db.cursor() as cursor:
        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_pw))
        db.commit()

def validate_user(email, password):
    user = find_user_by_email(email)
    if user and check_password_hash(user['password'], password):
        return user
    return None
