# app/routes/main_routes.py
from flask import Blueprint, render_template, jsonify, send_file, request
from app.utils.decorator import login_required
from app.database.connection import get_connection
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





def get_rows(building, floor, room, types, limit=50): # hàm có tên get_rows, nhận tham số giới hạn số dòng trả về "limit" (mặc định là 100).
    conn = get_connection() # **DB là cú pháp giải nén từ dictionary thành các đối số riêng lẻ cho hàm pymysql.connect().

    print(f"input trong get_rows la: {building},{floor}, {room}, {types}")
    # with ... as cur::  Đây là cú pháp quản lý ngữ cảnh (context manager), 
    # giúp đảm bảo rằng tài nguyên (ở đây là cursor) sẽ được đóng (close) đúng cách sau khi sử dụng xong, kể cả khi có lỗi xảy ra.
    # Khi khối with kết thúc, cur.close() sẽ được gọi tự động, giúp tránh rò rỉ tài nguyên.
    with conn.cursor() as cur:

        # iterable các tham số: là list, tuple, string, set, dict... là các đối tượng có thể lặp qua từng phần tử
        # cur.execute cần truyền vào 1 iterable để thay thế lần lượt vào %s trong câu lệnh SQL theo thứ tự
        # nếu chỉ có 1 phần tử, cần thêm "," để thư viện biết đó là tuple
        # cur.execute("SELECT datetime, temp, humid FROM temp_humid_data ORDER BY datetime DESC LIMIT %s", (limit,))
        

        
        # ['%s'] * len(types) → tạo ra một list gồm nhiều %s, đúng bằng số phần tử trong types
        # ','.join(...) → nối các phần tử trong list bằng dấu ,
        # Kết quả type_placeholders là một chuỗi như:  '%s' nếu có 1 loại; '%s,%s' nếu có 2 loại
        type_placeholders = ','.join(['%s'] * len(types))

        query = f"""
            SELECT 
                sd.timestamp, 
                sd.data_value, 
                sd.data_type, 
                sl.sensor_id
            FROM 
                sensor_data sd
            JOIN 
                sensor_location sl ON sd.sensor_id = sl.sensor_id
            WHERE 
                sl.building = %s AND
                sl.floor = %s AND 
                sl.room = %s AND 
                sd.data_type IN ({type_placeholders})
            ORDER BY 
                sd.timestamp DESC
            LIMIT %s;
        """
        params = (building, floor, room, *types, limit) # Tạo tuple chứa các tham số: floor, room, *types, limit
        cur.execute(query, params)
        rows = cur.fetchall() # lấy tất cả dòng kết quả.
    # ko cần gọi cur.close() vì đã được gọi tự động

    conn.close() 
    return rows[::-1] # đảo ngược kết quả để dòng cũ nhất ở đầu → phục vụ cho biểu đồ thời gian.

@main_bp.route('/get_data')
def data(): # Trả về JSON chứa dữ liệu để vẽ biểu đồ.
    building = request.args.get('building')
    floor = request.args.get('floor')
    room = request.args.get('room')
    types = request.args.getlist('type')

    rows = get_rows(building, floor, room, types)
    print(f"lấy được: {len(rows)}")
    # Dùng defaultdict để gom dữ liệu theo loại
    data_dict = defaultdict(list)
    labels = []

    for row in rows: # với mỗi row trong rows
        # lấy timestamp
        print(f"timestamp: {row['timestamp']}")
        ts = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        # nếu chưa có, lưu timestamp đó vào labels (nhãn của trục hoành trên đồ thị)
        if ts not in labels:
            labels.append(ts)
        # thêm data_value tương ứng với data_type vào data_dict
        data_dict[row['data_type']].append(row['data_value'])

    # Tạo JSON trả về
    response = {
        # gán labels là danh sách cho 'labels'
        # ví dụ:   "labels": ["2025-08-02 08:00:00","2025-08-02 08:10:00","2025-08-02 08:20:00",...]
        'labels': labels, 
    }

    for dtype in types: # với mỗi kiểu dữ liệu (dtype)
        # gán giá trị của mảng data(dtype,[]) làm danh sách cho dtype
        # ví dụ: "temperature": [25.2, 25.4, 25.6], "humidity": [60.1, 59.8, 60.3], ...
        response[dtype] = data_dict.get(dtype, [])
    print(f"Đã gửi cho client json:{response}")
    return jsonify(response)

# @main_bp.route('/temp_humid_chart')
# def chart(): # Trả về file HTML tĩnh cho người dùng xem biểu đồ.
#     return send_file('temp_humid_chart.html')