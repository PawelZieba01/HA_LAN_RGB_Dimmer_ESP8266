import ESP_uNetwork
from ESP_uRGBDimmer import ESP_uRGBDimmer
from time import sleep,time
import network

print("Starting main.py...........")

MyNet = ESP_uNetwork.ESP_uNetwork()
MyNet.set_net_config("bestconnect.pl 130", "pawel130", "192.168.1.60", "192.168.1.1")
MyNet.connect_to_AP()

import webrepl
webrepl.start()

DimmerRGB = ESP_uRGBDimmer("config.json")

client = DimmerRGB.connect_and_subscribe()
DimmerRGB.update_states()

while True:
    client.check_msg()
    # sleep(1)
    # print("dziala")