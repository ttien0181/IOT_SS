# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

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
        password = generate_password_hash(request.form['password'])

        # Lấy kết nối đến cơ sở dữ liệu
        db = get_connection()
        # Sử dụng 'with' để đảm bảo cursor được đóng đúng cách sau khi sử dụng
        with db.cursor() as cursor:
            # Kiểm tra xem email đã tồn tại trong cơ sở dữ liệu chưa
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            # Nếu tìm thấy người dùng với email này
            if cursor.fetchone():
                # Hiển thị thông báo lỗi nếu email đã được đăng ký
                flash("Email đã từng được đăng ký.")
                # Chuyển hướng người dùng trở lại trang đăng ký
                return redirect(url_for('auth.register'))
            # Nếu email chưa tồn tại, thêm người dùng mới vào cơ sở dữ liệu
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            # Lưu thay đổi vào cơ sở dữ liệu
            db.commit()
        # Hiển thị thông báo thành công sau khi đăng ký
        flash("Đăng ký thành công!")
        # Chuyển hướng người dùng đến trang đăng nhập
        return redirect(url_for('auth.login'))
    # Nếu yêu cầu là GET, hiển thị trang đăng ký
    return render_template('register.html')

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

        # Lấy kết nối đến cơ sở dữ liệu
        db = get_connection()
        with db.cursor() as cursor:
            # Truy vấn người dùng bằng email
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            # Kiểm tra xem người dùng có tồn tại không và mật khẩu có khớp không
            # check_password_hash sẽ so sánh mật khẩu người dùng nhập với mật khẩu đã mã hóa
            if user and check_password_hash(user['password'], password):
                # Nếu đăng nhập thành công, lưu ID người dùng vào session
                session['user_id'] = user['id']
                # Chuyển hướng người dùng đến trang chính (hoặc trang index)
                return redirect(url_for('index'))
            # Nếu email hoặc mật khẩu không đúng, hiển thị thông báo lỗi
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