# from rasp or client
import requests
import random
import time
import datetime
from email.message import EmailMessage

#API Key
API_KEY = "QFXS1F2D77UCKYDC"
# channel id (ID của Channel có tên iot-02)
CHANNEL_ID = "3005604"


# lấy dữ liệu về
def get_data():
    num_results = 5 # số lượng bản ghi cần lấy
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={API_KEY}&results={num_results}"
    response = requests.get(url) # nhận kết quả 
    data = response.json() # chuyển kết quả thành json
    feeds = data["feeds"] # lấy danh sách các bản ghi

    for i, feed in enumerate(feeds):
        field1 = feed.get("field1", "N/A") #lấy giá trị 'field1' của bản ghi, trả về N/A nếu ko có
        field2 = feed.get("field2", "N/A")

        print(f"Bản ghi {i+1}:")
        print(f"  - field1 (Temperature): {field1}")
        print(f"  - field2 (Pressure): {field2}")
        print()


get_data()