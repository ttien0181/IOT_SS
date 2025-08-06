# app/routes/main_routes.py
from flask import Blueprint, render_template, jsonify, send_file, request
from app.utils.decorator import login_required
from collections import defaultdict

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/floor/<int:floor_id>')
@login_required
def floor_page(floor_id):
    return render_template('floor.html', floor_id=floor_id)

@main_bp.route('/user')
@login_required
def user():
    return render_template('user.html')

@main_bp.route('/dashboard/<building>/<floor>/<room>')
@login_required
def dashboard(building,floor, room):
    return render_template('dashboard.html',building = building, floor=floor, room = room)



# def get_rows(building, floor, room, types, limit=50): # hàm có tên get_rows, nhận tham số giới hạn số dòng trả về "limit" (mặc định là 100).
#     conn = get_connection() # **DB là cú pháp giải nén từ dictionary thành các đối số riêng lẻ cho hàm pymysql.connect().

#     print(f"input trong get_rows la: {building},{floor}, {room}, {types}")
#     # with ... as cur::  Đây là cú pháp quản lý ngữ cảnh (context manager), 
#     # giúp đảm bảo rằng tài nguyên (ở đây là cursor) sẽ được đóng (close) đúng cách sau khi sử dụng xong, kể cả khi có lỗi xảy ra.
#     # Khi khối with kết thúc, cur.close() sẽ được gọi tự động, giúp tránh rò rỉ tài nguyên.
#     with conn.cursor() as cur:

#         # iterable các tham số: là list, tuple, string, set, dict... là các đối tượng có thể lặp qua từng phần tử
#         # cur.execute cần truyền vào 1 iterable để thay thế lần lượt vào %s trong câu lệnh SQL theo thứ tự
#         # nếu chỉ có 1 phần tử, cần thêm "," để thư viện biết đó là tuple
#         # cur.execute("SELECT datetime, temp, humid FROM temp_humid_data ORDER BY datetime DESC LIMIT %s", (limit,))
        

        
#         # ['%s'] * len(types) → tạo ra một list gồm nhiều %s, đúng bằng số phần tử trong types
#         # ','.join(...) → nối các phần tử trong list bằng dấu ,
#         # Kết quả type_placeholders là một chuỗi như:  '%s' nếu có 1 loại; '%s,%s' nếu có 2 loại
#         type_placeholders = ','.join(['%s'] * len(types))

#         query = f"""
#             SELECT 
#                 sd.timestamp, 
#                 sd.data_value, 
#                 sd.data_type, 
#                 sl.sensor_id
#             FROM 
#                 sensor_data sd
#             JOIN 
#                 sensor_location sl ON sd.sensor_id = sl.sensor_id
#             WHERE 
#                 sl.building = %s AND
#                 sl.floor = %s AND 
#                 sl.room = %s AND 
#                 sd.data_type IN ({type_placeholders})
#             ORDER BY 
#                 sd.timestamp DESC
#             LIMIT %s;
#         """
#         params = (building, floor, room, *types, limit) # Tạo tuple chứa các tham số: floor, room, *types, limit
#         cur.execute(query, params)
#         rows = cur.fetchall() # lấy tất cả dòng kết quả.
#     # ko cần gọi cur.close() vì đã được gọi tự động

#     conn.close() 
#     return rows[::-1] # đảo ngược kết quả để dòng cũ nhất ở đầu → phục vụ cho biểu đồ thời gian.

