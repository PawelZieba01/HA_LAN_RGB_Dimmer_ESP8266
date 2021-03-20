import ESP_uNetwork
from ESP_uRGBDimmer import ESP_uRGBDimmer
from utime import sleep, ticks_ms
from machine import Pin


print("Starting main.py...........")

myNet = ESP_uNetwork.ESP_uNetwork()
myNet.set_net_config("bestconnect.pl 130", "pawel130", "192.168.1.60", "192.168.1.1")
myNet.connect_to_AP()

# import webrepl
# webrepl.start()

dimmerRGB = ESP_uRGBDimmer("config.json")

dimmerRGB.connect_and_subscribe()
dimmerRGB.update_states()


led = Pin(2, Pin.OUT)
led.value(1)






while True:
    dimmerRGB.get_mqtt_data()       # pobranie wiadomości z serwera i wykonanie poleceń
    dimmerRGB.let_there_be_light()











