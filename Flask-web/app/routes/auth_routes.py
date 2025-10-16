# auth_routers.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user_model import find_user_by_email, validate_user, request_register, confirm_otp

# Tạo một Blueprint cho các route xác thực.
# Blueprint giúp tổ chức các route và module code của ứng dụng.
auth_bp = Blueprint('auth', __name__)

# ---
## Route đăng ký người dùng
# Xử lý cả yêu cầu GET (hiển thị form) và POST (xử lý dữ liệu form).
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Kiểm tra nếu yêu cầu là POST (người dùng đã gửi form đăng ký)
    if request.method == 'POST':
        # Lấy email từ dữ liệu form
        email = request.form['email']
        # Mã hóa mật khẩu trước khi lưu vào cơ sở dữ liệu để bảo mật
        password = request.form['password']

        # nếu thấy email -> email đã từng dùng
        if find_user_by_email(email):
            flash("Email đã từng được đăng ký.")
            return redirect(url_for('auth.register'))
        
        # nếu ko, đưa về trang confirm_register chờ nhập OTP
        request_register(email, password)
        flash("Mã xác nhận đã được gửi đến email của bạn. Vui lòng nhập OTP để hoàn tất đăng ký.")
        return redirect(url_for('auth.confirm_register', email=email))
    
    # Nếu yêu cầu là GET, hiển thị trang đăng ký
    return render_template('register.html')

@auth_bp.route('/confirm_register', methods=['GET', 'POST'])
def confirm_register():
    email = request.args.get('email')  # Lấy email từ URL query

    if request.method == 'POST':
        otp = request.form['otp']
        if confirm_otp(email, otp):
            flash("Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect(url_for('auth.login'))
        else:
            flash("Mã xác nhận không đúng hoặc đã hết hạn.")
            return redirect(url_for('auth.confirm_register', email=email))

    return render_template('confirm_register.html', email=email)


# ---
## Route đăng nhập người dùng
# Xử lý cả yêu cầu GET (hiển thị form) và POST (xử lý dữ liệu form).
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Kiểm tra nếu yêu cầu là POST (người dùng đã gửi form đăng nhập)
    if request.method == 'POST':
        # Lấy email và mật khẩu từ dữ liệu form
        email = request.form['email']
        password = request.form['password']

        user = validate_user(email, password)
        if user:
            print("Session before login:", session)
            session['user_id'] = user['id']
            session['email'] = user['email']
            created_value = user.get('create_at') or user.get('created_at')
            if created_value and hasattr(created_value, 'strftime'):
                created_str = created_value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session['create_at'] = created_str
            print("Session after login:", session)
            return redirect(url_for('main.index'))
        
        flash("Sai email hoặc mật khẩu")
    # Nếu yêu cầu là GET, hiển thị trang đăng nhập
    return render_template('login.html')



# ---
## Route đăng xuất người dùng
@auth_bp.route('/logout')
def logout():
    # Xóa tất cả dữ liệu trong session để đăng xuất người dùng
    session.clear()
    # Chuyển hướng người dùng về trang đăng nhập
    return redirect(url_for('auth.login'))



