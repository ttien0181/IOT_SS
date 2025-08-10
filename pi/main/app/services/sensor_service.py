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