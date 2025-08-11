# connection.py
import pymysql

def get_mobiusdb_connection():
    return pymysql.connect(
        host="localhost",      # hoặc IP nếu server khác
        user="root",
        password="mobius",
        db="mobiusdb",            # tên CSDL bạn đã tạo
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_iot02_connection():
    return pymysql.connect(
        host="localhost",      # hoặc IP nếu server khác
        user="ttien",
        password="0181",
        db="iot02",            # tên CSDL bạn đã tạo
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
