from umqtt_simple import MQTTClient
import json
from machine import Pin, PWM
import machine


class ESP_uRGBDimmer:

    def __init__(self, config_file_dir = ""):
        if (config_file_dir):

            #zmienne klasy
            self.rgbw = [50, 50, 50, 50]  # wartości kolorów rgbw
            self.brightness = 100  # jasność (0-100%)
            self.status = b'OFF'  # światło włączone / wyłączone

            #pobranie konfiguracji z pliku
            print("Opening config file: 'conf.json'")
            f = open(config_file_dir, "r")
            config_json = f.read()                  #pobranie danych konfiguracyjnych z pliku config.json
            config_dict = json.loads(config_json)   #zdekodowanie danych json - zamiana na dictionary
            f.close()
            del config_json

            #pobranie danych z dictionary
            self.pin_R = int(config_dict["pin_R"])
            self.pin_G = int(config_dict["pin_G"])
            self.pin_B = int(config_dict["pin_B"])
            self.pin_W = int(config_dict["pin_W"])

            self.pwm_R = PWM(Pin(self.pin_R))
            self.pwm_G = PWM(Pin(self.pin_G))
            self.pwm_B = PWM(Pin(self.pin_B))
            self.pwm_W = PWM(Pin(self.pin_W))

            self.client_id = config_dict["client_id"].encode('utf-8')
            self.topic_sub_state = config_dict["topic_sub_state"].encode('utf-8')
            self.topic_pub_state = config_dict["topic_pub_state"].encode('utf-8')
            self.topic_sub_brightness = config_dict["topic_sub_brightness"].encode('utf-8')
            self.topic_pub_brightness = config_dict["topic_pub_brightness"].encode('utf-8')
            self.topic_sub_rgb = config_dict["topic_sub_rgb"].encode('utf-8')
            self.topic_pub_rgb = config_dict["topic_pub_rgb"].encode('utf-8')
            self.topic_sub_white = config_dict["topic_sub_white"].encode('utf-8')
            self.topic_pub_white = config_dict["topic_pub_white"].encode('utf-8')

            self.mqtt_server = config_dict["mqtt_server"]
            self.mqtt_port = int(config_dict["mqtt_port"])
            self.mqtt_user = config_dict["mqtt_user"]
            self.mqtt_pass = config_dict["mqtt_pass"]

            del config_dict

    #funkcja łącząca się z brokerem i subskrybująca tematy
    def connect_and_subscribe(self):
        self.client = MQTTClient(self.client_id, self.mqtt_server, self.mqtt_port, self.mqtt_user, self.mqtt_pass)
        self.client.set_callback(self.__mqtt_handler)
        self.client.connect()

        #subskrybcja tematów mqtt
        self.client.subscribe(self.topic_sub_state)
        self.client.subscribe(self.topic_sub_brightness)
        self.client.subscribe(self.topic_sub_rgb)
        self.client.subscribe(self.topic_sub_white)

        print('Connected to MQTT broker.')
        return self.client

    #funkcja przetwarzająca dane pobrane z brokera
    def __mqtt_handler(self, topic, msg):
        print((topic, msg))

        #odebrano wiadomość ze stanem
        if(topic == self.topic_sub_state):
            self.status = msg

        #odebrano wiadomość z jasnością
        elif(topic == self.topic_sub_brightness):
            if(int(msg) < 2):
                self.brightness = 0
            else:
                self.brightness = int(msg)

        #odebrano wiadomość z kolorem rgb
        elif(topic == self.topic_sub_rgb):
            rgb = msg.decode().split(',')
            self.rgbw[0] = int(rgb[0])
            self.rgbw[1] = int(rgb[1])
            self.rgbw[2] = int(rgb[2])

        # odebrano wiadomość z wartością bieli
        elif(topic == self.topic_sub_white):
            self.rgbw[3] = int(msg)

        #wyłączenie światła gdy jasność ustawiona na 0
        if(self.brightness == 0):
            self.status = b'OFF'

        self.update_states()            #aktualizacja stanów na serwerze
        self.set_pwm()                  #ustawienie wartości PWM

    #funkcja aktualizująca dane na serwerze
    def update_states(self):
        #przygotowanie danych
        status_val = self.status
        brightness_val = bytes(str(self.brightness), 'utf-8')
        rgb_val = bytes(str(self.rgbw[0]) +','+ str(self.rgbw[1]) +','+ str(self.rgbw[2]), 'utf-8')
        white_val = bytes(str(self.rgbw[3]), 'utf-8')

        #wysłanie danych
        self.client.publish(self.topic_pub_brightness, brightness_val)
        self.client.publish(self.topic_pub_rgb, rgb_val)
        self.client.publish(self.topic_pub_white, white_val)
        self.client.publish(self.topic_pub_state, status_val)

    #funkcja włączająca PWM
    def set_pwm(self):
        #włączenie światła
        if(self.status == b'ON'):
            self.pwm_R.duty(int(self.rgbw[0] * 0.04 * self.brightness))
            self.pwm_G.duty(int(self.rgbw[1] * 0.04 * self.brightness))
            self.pwm_B.duty(int(self.rgbw[2] * 0.04 * self.brightness))
            self.pwm_W.duty(int(self.rgbw[3] * 0.04 * self.brightness))

        #wyłączenie światła
        else:
            self.pwm_R.duty(0)
            self.pwm_G.duty(0)
            self.pwm_B.duty(0)
            self.pwm_W.duty(0)

        #print(self.pwm_R.duty(), self.pwm_G.duty(), self.pwm_B.duty(), self.pwm_W.duty())
