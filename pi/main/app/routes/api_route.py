from flask import Blueprint, jsonify, request
from collections import defaultdict
from app.services.sensor_service import get_rows


# 'api': Tên của Blueprint, Flask dùng để phân biệt với các Blueprint khác.
# __name__: Là module hiện tại, giúp Flask xác định đường dẫn template hoặc static nếu có.
# url_prefix='/api': Đây là đường dẫn gốc (prefix) cho tất cả route nằm trong Blueprint này.
# mọi route được khai báo trong api_bp sẽ tự động thêm /api ở đầu URL.
api_bp = Blueprint('api', __name__, url_prefix='/api') 

@api_bp.route('/get_data')
def get_data(): # Trả về JSON chứa dữ liệu để vẽ biểu đồ.
    building = request.args.get('building')
    floor = request.args.get('floor')
    room = request.args.get('room')
    types = request.args.getlist('type')
    limit = int(request.args.get('limit'))

    rows = get_rows(building, floor, room, types, limit)
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
        data_dict[row['data_type']].append(row['value'])

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