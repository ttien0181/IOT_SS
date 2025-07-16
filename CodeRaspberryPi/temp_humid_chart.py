#!/usr/bin/env python3 # cho phép chạy mà ko cần gọi python3 rõ ràng
from flask import Flask, jsonify, send_file
import pymysql

app = Flask(__name__)

DB = dict(host='localhost', user='ttien', password='0181', db='iot02',
          charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

def get_rows(limit=100): # hàm có tên get_rows, nhận tham số giới hạn số dòng trả về "limit" (mặc định là 100).
    conn = pymysql.connect(**DB) # **DB là cú pháp giải nén từ dictionary thành các đối số riêng lẻ cho hàm pymysql.connect().

    # with ... as cur::  Đây là cú pháp quản lý ngữ cảnh (context manager), 
    # giúp đảm bảo rằng tài nguyên (ở đây là cursor) sẽ được đóng (close) đúng cách sau khi sử dụng xong, kể cả khi có lỗi xảy ra.
    # Khi khối with kết thúc, cur.close() sẽ được gọi tự động, giúp tránh rò rỉ tài nguyên.
    with conn.cursor() as cur:

        # iterable các tham số: là list, tuple, string, set, dict... là các đối tượng có thể lặp qua từng phần tử
        # cur.execute cần truyền vào 1 iterable để thay thế lần lượt vào %s trong câu lệnh SQL theo thứ tự
        # nếu chỉ có 1 phần tử, cần thêm "," để thư viện biết đó là tuple
        cur.execute("SELECT datetime, temp, humid FROM dht_data ORDER BY datetime DESC LIMIT %s", (limit,))
        
        
        rows = cur.fetchall() # lấy tất cả dòng kết quả.
    # ko cần gọi cur.close() vì đã được gọi tự động

    conn.close() 
    return rows[::-1] # đảo ngược kết quả để dòng cũ nhất ở đầu → phục vụ cho biểu đồ thời gian.

@app.route('/temp_humid_data')
def data(): # Trả về JSON chứa dữ liệu để vẽ biểu đồ.
    rows = get_rows()
    return jsonify({ # Đây là câu lệnh trả về một đối tượng JSON dưới dạng phản hồi HTTP từ Flask.
        # lấy giá trị có nhãn 'datetime' với mỗi dict trong rows, chuyển về %Y-%m-%d %H:%M:%S và tạo ra danh sách 'labels'
        'labels':[r['datetime'].strftime('%Y-%m-%d %H:%M:%S') for r in rows], 
        # lấy giá trị có nhãn 'temp' với mỗi dict trong rows, tạo ra danh sách 'times'
        'temps':[r['temp'] for r in rows],
        # lấy giá trị có nhãn 'humid' với mỗi dict trong rows, tạo ra danh sách 'humids'
        'humids':[r['humid'] for r in rows]

        # ví dụ có rows là danh sách các dict, như sau:
        # rows = [
        #     {'datetime': datetime.datetime(2025, 7, 15, 15, 40), 'temp': 28.5, 'humid': 65.0},
        #     {'datetime': datetime.datetime(2025, 7, 15, 15, 45), 'temp': 28.6, 'humid': 64.8},
        #     {'datetime': datetime.datetime(2025, 7, 15, 15, 50), 'temp': 28.4, 'humid': 66.0},
        # ]
        # sau khi chuyển thanh json thì sẽ như sau
        # {
        #   "labels": ["2025-07-15 15:40:00", "2025-07-15 15:45:00", "2025-07-15 15:50:00"],
        #   "temps": [28.5, 28.6, 28.4],
        #   "humids": [65.0, 64.8, 66.0]
        # }

    })

@app.route('/temp_humid_chart')
def chart(): # Trả về file HTML tĩnh cho người dùng xem biểu đồ.
    return send_file('temp_humid_chart.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
