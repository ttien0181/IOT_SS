# from rasp or client
import requests
import random
import time
import datetime
from email.message import EmailMessage

#API Key
API_KEY = "QFXS1F2D77UCKYDC"
# channel id (ID của Channel có tên ID 2)
CHANNEL_ID = "3005604"



def get_data():
    num_results = 5 # số lượng bản ghi cần lấy
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={API_KEY}&results={num_results}"
    response = requests.get(url)   
    data = response.json()
    feeds = data["feeds"]

    for i, feed in enumerate(feeds):
        field1 = feed.get("field1", "N/A")
        field2 = feed.get("field2", "N/A")
        
        if field1 > 15:
            send_email()

        print(f"Bản ghi {i+1}:")
        print(f"  - field1 (Tempurature ): {field1}")
        print(f"  - field2 (Pressure): {field2}")
        print()


get_data()