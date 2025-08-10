# Decorator là gì?
#   Trong Python, decorator là một hàm nhận vào một hàm khác và trả về một hàm mới.
#   Nó cho phép bạn chèn thêm logic trước hoặc sau khi thực thi hàm gốc, mà không cần sửa đổi hàm gốc.

from functools import wraps
from flask import redirect, url_for, session

# "bao bọc" hàm gốc (vẫn giả danh hàm gốc), chỉ thực hiện hàm gốc khi hàm gốc được "return"
def login_required(f):
    # sao chép metadata từ hàm gốc 'f' sang hàm được bao bọc 'decorated_function'
    # tránh che mất __name__ (tên hàm gốc), __doc__ (phần ghi chú (docstring)), __module__, __annotations__ ...
    @wraps(f) 
    # *args	Thu thập tất cả đối số không đặt tên (kiểu tuple).
    # **kwargs	Thu thập tất cả đối số có tên (kiểu dictionary).
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # nếu chưa có session thì đưa về /login
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs) # nếu ok, "trả lại" func gốc
    return decorated_function
