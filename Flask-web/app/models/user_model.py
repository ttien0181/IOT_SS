# app/models/user_model.py
import random
import smtplib
import datetime
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.connection import get_iot02_connection

# gửi email chứa OTP tới người dùng
def send_verification_email(to_email, otp):
    msg = MIMEText(f"Mã xác nhận đăng ký của bạn là: {otp}")
    msg["Subject"] = "Xác nhận đăng ký"
    msg["From"] = "ttien0181@gmail.com"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("ttien0181@gmail.com", "hxqt hvmh bjhu jrmw")
        server.send_message(msg)

# khi nhận yêu cầu đăng ký, sẽ tạo otp (lưu trong bảng tạm), sau đó gửi email chứa OTP tới người dùng
def request_register(email, password):
    db = get_iot02_connection()
    otp = str(random.randint(100000, 999999))
    hashed_pw = generate_password_hash(password)
    expires = datetime.datetime.now() + datetime.timedelta(minutes=5)
    with db.cursor() as cursor:
        # Nếu email đã tồn tại trong bảng pending_users thì ghi đè (cập nhật OTP mới).
        cursor.execute(
            "REPLACE INTO pending_users (email, password_hash, otp_code, expires_at) VALUES (%s, %s, %s, %s)",
            (email, hashed_pw, otp, expires)
        )
        db.commit()
    # gửi email tới người dùng
    send_verification_email(email, otp)

# xác nhận OTP có đúng ko, nếu đúng thì tạo user
def confirm_otp(email, otp):
    db = get_iot02_connection()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pending_users WHERE email=%s AND otp_code=%s AND expires_at > NOW()", (email, otp))
        row = cursor.fetchone()
        if row:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, row['password_hash']))
            cursor.execute("DELETE FROM pending_users WHERE email=%s", (email,))
            db.commit()
            return True
    return False

# tìm user theo email
def find_user_by_email(email):
    db = get_iot02_connection()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        return cursor.fetchone()

# xác nhận user đúng hay sai
def validate_user(email, password):
    user = find_user_by_email(email)
    # nếu tìm thấy user và password đúng thì trả về user đó
    if user and check_password_hash(user['password'], password):
        return user
    return None
