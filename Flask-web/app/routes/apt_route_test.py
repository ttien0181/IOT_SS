from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from collections import defaultdict
from app.services.sensor_service import get_rows

# Khởi tạo Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Khởi tạo API của Flask-RESTful và liên kết với Blueprint
api = Api(api_bp)

# Định nghĩa các tham số đầu vào cho API
# reqparse giúp việc xác thực và phân tích cú pháp các tham số request trở nên dễ dàng và rõ ràng hơn.
parser = reqparse.RequestParser()
parser.add_argument('building', type=str, required=True, help='Building is required')
parser.add_argument('floor', type=str, required=True, help='Floor is required')
parser.add_argument('room', type=str, required=True, help='Room is required')
parser.add_argument('types', type=str, action='append', required=True, help='At least one type is required')
parser.add_argument('limit', type=int, default=10, help='Limit the number of records, default is 10')

# Tạo một lớp Resource để xử lý endpoint /get_data
class SensorData(Resource):
    # Định nghĩa phương thức GET
    def get(self):
        # Phân tích cú pháp các tham số từ request URL
        args = parser.parse_args()

        building = args['building']
        floor = args['floor']
        room = args['room']
        types = args['types']
        limit = args['limit']

        rows = get_rows(building, floor, room, types, limit)
        print(f"lấy được: {len(rows)}")

        # Gom dữ liệu
        data_dict = defaultdict(list)
        labels = []

        for row in rows:
            ts = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            if ts not in labels:
                labels.append(ts)
            data_dict[row['data_type']].append(row['value'])
        
        # Tạo JSON response
        response = {
            'labels': labels,
        }
        
        for dtype in types:
            response[dtype] = data_dict.get(dtype, [])

        print(f"Đã gửi cho client json:{response}")
        # Flask-RESTful tự động chuyển đổi từ điển này thành JSON response
        return response

# Thêm Resource vào API và chỉ định URL
api.add_resource(SensorData, '/get_data')


# Đoạn code bạn cung cấp là một ví dụ về cách tạo một API bằng Flask-RESTful để lấy dữ liệu cảm biến. Dưới đây là giải thích chi tiết từng phần của mã nguồn:

# 1. Khai báo các thư viện cần thiết
# Python

# from flask import Blueprint
# from flask_restful import Api, Resource, reqparse
# from collections import defaultdict
# from app.services.sensor_service import get_rows
# Flask: Khung web chính.

# Blueprint: Giúp tổ chức ứng dụng Flask thành các module nhỏ, có thể tái sử dụng.

# Flask-RESTful: Một tiện ích mở rộng của Flask giúp xây dựng các API RESTful một cách nhanh chóng và dễ dàng. Nó cung cấp các lớp (như Resource, Api, reqparse) để xử lý các yêu cầu HTTP.

# defaultdict: Một lớp từ module collections trong Python. Nó giống như dict nhưng có thêm một tính năng: khi bạn truy cập một khóa không tồn tại, nó sẽ tự động tạo ra một giá trị mặc định cho khóa đó (ví dụ: một danh sách rỗng).

# get_rows: Một hàm được import từ một module khác (app.services.sensor_service). Hàm này chịu trách nhiệm lấy dữ liệu từ cơ sở dữ liệu dựa trên các tham số đầu vào.

# 2. Khởi tạo Blueprint và API
# Python

# # Khởi tạo Blueprint
# api_bp = Blueprint('api', __name__, url_prefix='/api')

# # Khởi tạo API của Flask-RESTful và liên kết với Blueprint
# api = Api(api_bp)
# api_bp = Blueprint('api', __name__, url_prefix='/api'): Tạo một Blueprint mới có tên là 'api'. Tất cả các route (đường dẫn) được định nghĩa trong Blueprint này sẽ có tiền tố là /api.

# api = Api(api_bp): Tạo một đối tượng Api và liên kết nó với api_bp. Điều này có nghĩa là tất cả các tài nguyên (Resource) của API sẽ được thêm vào Blueprint này.

# 3. Định nghĩa và phân tích các tham số đầu vào
# Python

# parser = reqparse.RequestParser()
# parser.add_argument('building', type=str, required=True, help='Building is required')
# parser.add_argument('floor', type=str, required=True, help='Floor is required')
# parser.add_argument('room', type=str, required=True, help='Room is required')
# parser.add_argument('types', type=str, action='append', required=True, help='At least one type is required')
# parser.add_argument('limit', type=int, default=10, help='Limit the number of records, default is 10')
# reqparse.RequestParser(): Tạo một đối tượng parser để xử lý và xác thực các tham số từ yêu cầu HTTP (thường là từ URL query string, ví dụ: /api/get_data?building=A&floor=1).

# parser.add_argument(): Thêm các tham số mà API này mong đợi:

# 'building', 'floor', 'room': Các tham số bắt buộc (required=True), phải là kiểu chuỗi (type=str). Nếu thiếu một trong số này, API sẽ trả về lỗi.

# 'types': Tham số này có action='append', nghĩa là nó có thể nhận nhiều giá trị (ví dụ: ?types=temperature&types=humidity). Các giá trị này sẽ được thêm vào một danh sách.

# 'limit': Tham số tùy chọn, kiểu số nguyên (type=int), có giá trị mặc định là 10 (default=10).

# 4. Định nghĩa Tài nguyên (Resource)
# Python

# class SensorData(Resource):
#     def get(self):
#         # ... logic xử lý ...
# class SensorData(Resource): Tạo một lớp Python kế thừa từ flask_restful.Resource. Mỗi lớp Resource đại diện cho một tài nguyên API (trong trường hợp này là dữ liệu cảm biến).

# def get(self): Phương thức này xử lý các yêu cầu HTTP GET đến endpoint. Các phương thức khác như post(), put(), delete() cũng có thể được định nghĩa để xử lý các loại yêu cầu khác.

# 5. Logic xử lý trong phương thức get
# Python

# # Phân tích cú pháp các tham số từ request URL
# args = parser.parse_args()
# building = args['building']
# floor = args['floor']
# # ... và các tham số khác
# args = parser.parse_args(): Lệnh này thực hiện việc phân tích các tham số từ URL dựa trên các quy tắc đã định nghĩa trong parser. Nếu các tham số không hợp lệ (ví dụ: thiếu tham số bắt buộc), nó sẽ tự động trả về một lỗi 400 Bad Request.

# Python

# rows = get_rows(building, floor, room, types, limit)
# Gọi hàm get_rows để lấy dữ liệu từ cơ sở dữ liệu hoặc một nguồn dữ liệu khác. Hàm này trả về một danh sách các bản ghi (row), mỗi bản ghi có thể là một từ điển.

# Python

# # Gom dữ liệu
# data_dict = defaultdict(list)
# labels = []
# for row in rows:
#     ts = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
#     if ts not in labels:
#         labels.append(ts)
#     data_dict[row['data_type']].append(row['value'])
# Đây là phần xử lý chính để định dạng lại dữ liệu.

# data_dict = defaultdict(list): Khởi tạo một từ điển, trong đó mỗi giá trị mặc định là một danh sách rỗng.

# Vòng lặp for row in rows duyệt qua từng bản ghi dữ liệu đã lấy được.

# ts = row['timestamp'].strftime(...): Chuyển đổi đối tượng thời gian (datetime hoặc tương tự) thành một chuỗi có định dạng dễ đọc.

# labels.append(ts): Thu thập tất cả các mốc thời gian duy nhất để sử dụng làm nhãn (labels) cho biểu đồ.

# data_dict[row['data_type']].append(row['value']): Dòng code này rất quan trọng. Nó nhóm dữ liệu theo loại cảm biến (data_type). Ví dụ, nếu row['data_type'] là 'temperature', nó sẽ thêm giá trị 'value' vào danh sách ứng với khóa 'temperature' trong data_dict.

# Python

# # Tạo JSON response
# response = {
#     'labels': labels,
# }
# for dtype in types:
#     response[dtype] = data_dict.get(dtype, [])
# Tạo một từ điển response để trả về cho client.

# Thêm danh sách nhãn (labels) vào từ điển này.

# Vòng lặp for dtype in types duyệt qua danh sách các loại cảm biến mà người dùng đã yêu cầu.

# response[dtype] = data_dict.get(dtype, []): Lấy danh sách các giá trị tương ứng từ data_dict và gán vào từ điển response với khóa là tên loại cảm biến. Nếu một loại cảm biến không có dữ liệu, data_dict.get(dtype, []) sẽ trả về một danh sách rỗng, đảm bảo cấu trúc của phản hồi luôn nhất quán.

# Python

# return response
# return response: Lệnh này trả về từ điển response. Flask-RESTful sẽ tự động chuyển đổi từ điển này thành một phản hồi JSON và gửi về cho client.

# 6. Thêm tài nguyên vào API
# Python

# api.add_resource(SensorData, '/get_data')
# api.add_resource(SensorData, '/get_data'): Liên kết lớp SensorData với endpoint /get_data. Khi một yêu cầu đến /api/get_data (vì có url_prefix='/api' trong Blueprint), Flask-RESTful sẽ gọi các phương thức tương ứng (get, post,...) trong lớp SensorData để xử lý.