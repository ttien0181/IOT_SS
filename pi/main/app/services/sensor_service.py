# # sensor_service.py
# from app.database.connection import get_connection
# import pymysql

# # nhận tham số giới hạn số dòng trả về "limit" 
# def get_rows(building, floor, room, types, limit): 
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


# def get_latest_data(building, floor, room, data_type):
#     conn = get_connection()
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cur:
#             cur.execute("""
#                 SELECT sd.data_value, sd.data_type 
#                 FROM sensor_data sd
#                 JOIN sensor_location sl ON sd.sensor_id = sl.sensor_id
#                 WHERE sl.building = %s
#                   AND sl.floor = %s
#                   AND sl.room = %s
#                   AND sd.data_type = %s
#                 ORDER BY sd.timestamp DESC
#                 LIMIT 1;
#             """, (building, floor, room, data_type))
#             return cur.fetchone()
#     finally:
#         conn.close()




# sensor_service.py

from app.database.connection import get_mobiusdb_connection
from datetime import datetime
import pymysql
import json

def get_rows(building, floor, room, types, limit):
    conn = get_mobiusdb_connection()
    try:
        with conn.cursor() as cur:
            pi_prefix = f"/Mobius/HealthCare-SSIoT/{building}/{floor}/{room}/"
            
            # Tạo danh sách các điều kiện cho pi
            pi_conditions = ["pi LIKE %s" for _ in types]
            pi_sql = " OR ".join(pi_conditions)
            
            query = """
                SELECT pi, con
                FROM cin
                WHERE {}
                ORDER BY JSON_EXTRACT(con, '$.t') DESC
                LIMIT %s;
            """.format(pi_sql)
            
            # Chuẩn bị tham số: mỗi type sẽ có một chuỗi pi_prefix + type + '%'
            params_for_pi = [f"{pi_prefix}{t}%" for t in types]
            params = tuple(params_for_pi) + (limit,)
            
            cur.execute(query, params)
            rows = cur.fetchall()

            processed_rows = []
            for row in rows:
                pi = row['pi']
                con_str = row['con']
                # row_data = json.load(row)
                # pi = row_data.get('pi')
                # con_str = row_data('con') 
                try:
                    con_data = json.loads(con_str)
                    # Chuyển đổi chuỗi timestamp thành đối tượng datetime
                    timestamp_str = con_data.get('t')
                    # Loại bỏ 'Z' và sau đó parse
                    if timestamp_str and timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] # Loại bỏ 'Z'
                    parsed_timestamp = datetime.fromisoformat(timestamp_str)
                    
                    data_type = pi.split('/')[-1]
                    processed_rows.append({
                        'timestamp': parsed_timestamp,
                        'value': con_data.get('v'),
                        'unit': con_data.get('u'),
                        'sensor_id': con_data.get('sid'),
                        'data_type': data_type
                    })
                except json.JSONDecodeError as e:
                    print(f"Lỗi phân tích JSON: {e} trong dòng: {row}")
                    continue
            
            return processed_rows[::-1]
    finally:
        conn.close()




def get_latest_data(building, floor, room, data_type):
    conn = get_mobiusdb_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            pi_path = f'/Mobius/HealthCare-SSIoT/{building}/{floor}/{room}/{data_type}'
            
            cur.execute("""
                SELECT con
                FROM cin
                WHERE pi = %s
                ORDER BY JSON_EXTRACT(con, '$.t') DESC
                LIMIT 1;
            """, (pi_path,))
            
            row = cur.fetchone()
            
            if row:
                con_str = row['con']
                try:
                    con_data = json.loads(con_str)

                    return {
                        'timestamp': con_data.get('t'),
                        'value': con_data.get('v'),
                        'unit': con_data.get('u'),
                        'sensor_id': con_data.get('sid'),
                        'data_type': data_type
                    }
                except json.JSONDecodeError as e:
                    print(f"Lỗi phân tích JSON: {e}")
                    return None
            return None
    finally:
        conn.close()