#!/usr/bin/env python3 # cho phép chạy mà ko cần gọi python3 rõ ràng
import sys
# import Adafruit_DHT #  đọc cảm biến nhiệt độ và độ ẩm.
import pymysql
import time

def main():
    if len(sys.argv) != 3: # nếu ko đúng 3 đối số (VD: sys.argv = ['AdafruitDHT.py', '11', '2']) thì exit
        print("Usage: AdafruitDHT.py <sensor_type> <gpio_pin>")
        # sensor_type: kiểu cảm biến (ví dụ 11 cho DHT11).
        # gpio_pin: số chân GPIO được dùng để kết nối cảm biến (ví dụ 2).
        sys.exit(1)

    sensor_type = int(sys.argv[1])  # VD : 11
    gpio_pin = int(sys.argv[2])     # VD : 2

    # Connect to DB
    db = pymysql.connect(host='localhost', user='ttien', password='0181', db='iot02', charset='utf8mb4')
    
    try:
        cur = db.cursor() # make cursor to execute SQL query
        while True:
            # Read sensor: auto retry after 2s if read error(max 15 time)
            # humidity, temperature = Adafruit_DHT.read_retry(sensor_type, gpio_pin) 
            humidity, temperature = {5,4}
            if humidity is not None and temperature is not None: # if ok
                # Insert data
                sql = "INSERT INTO dht_data (datetime, temp, humid) VALUES (NOW(), %s, %s)"
                print(sql)
                cur.execute(sql, (temperature, humidity)) # execute the query
                db.commit() # Xác nhận ghi dữ liệu vào cơ sở dữ liệu (trong một transaction).
                print(f"Inserted: Temperature={temperature:.1f}C, Humidity={humidity:.1f}%")        
            else:
                print("Failed to retrieve data from sensor")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        cur.close()
        db.close()


# Kiểm tra nếu file này được chạy trực tiếp (python3 AdafruitDHT.py) thì sẽ gọi hàm main().
# đồng thời tránh chạy main() nếu file được import vào chương trình khác
if __name__ == "__main__": 
    main()
