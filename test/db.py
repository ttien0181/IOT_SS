# db.py
import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",      # hoặc IP nếu server khác
        user="ttien",
        password="0181",
        db="iot02",            # tên CSDL bạn đã tạo
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
