from umqtt_simple import MQTTClient
import json
from machine import Pin, PWM
import math
from utime import ticks_ms


class ESP_uRGBDimmer:

    def __init__(self, config_file_dir=""):
        if (config_file_dir):

            # zmienne klasy
            self.rgbw = [255, 255, 255, 0]  # wartości kolorów rgbw
            self.brightness = 50  # jasność (0-100%)
            self.status = b'OFF'  # światło włączone / wyłączone
            self.effect = b'solid'  # aktualny efekt

            self.counter = 0
            self.last_time_ms = 0
            self.last_brightness = 0

            # pobranie konfiguracji z pliku
            print("Opening config file: 'conf.json'")
            f = open(config_file_dir, "r")
            config_json = f.read()  # pobranie danych konfiguracyjnych z pliku config.json
            config_dict = json.loads(config_json)  # zdekodowanie danych json - zamiana na dictionary
            f.close()
            del config_json

            # pobranie danych z dictionary
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
            self.topic_sub_effect = config_dict["topic_sub_effect"].encode('utf-8')
            self.topic_pub_effect = config_dict["topic_pub_effect"].encode('utf-8')

            self.topic_pub_availability = config_dict["topic_pub_availability"].encode('utf-8')

            self.mqtt_server = config_dict["mqtt_server"]
            self.mqtt_port = int(config_dict["mqtt_port"])
            self.mqtt_user = config_dict["mqtt_user"]
            self.mqtt_pass = config_dict["mqtt_pass"]

            self.client = MQTTClient(self.client_id, self.mqtt_server, self.mqtt_port, self.mqtt_user, self.mqtt_pass)

            del config_dict

    # funkcja łącząca się z brokerem i subskrybująca tematy
    def connect_and_subscribe(self):
        self.client.set_callback(self.__mqtt_handler)
        self.client.connect()

        # wysłanie informacji o dostępności urządzenia
        self.client.publish(self.topic_pub_availability, "online")

        # subskrybcja tematów mqtt
        self.client.subscribe(self.topic_sub_state)
        self.client.subscribe(self.topic_sub_brightness)
        self.client.subscribe(self.topic_sub_rgb)
        self.client.subscribe(self.topic_sub_white)
        self.client.subscribe(self.topic_sub_effect)

        print('Connected to MQTT broker.')
        return self.client

    # funkcja pobierająca informacje z serwera i wykonująca polecenia z __mqtt_handler()
    def get_mqtt_data(self):
        self.client.check_msg()

    # funkcja przetwarzająca dane pobrane z brokera
    def __mqtt_handler(self, topic, msg):
        print((topic, msg))

        # odebrano wiadomość ze stanem
        if (topic == self.topic_sub_state):
            self.status = msg

        # odebrano wiadomość z jasnością
        elif (topic == self.topic_sub_brightness):
            # if (int(msg) < 2):
            #     self.brightness = 0
            # else:
            self.brightness = int(msg)

        # odebrano wiadomość z kolorem rgb
        elif (topic == self.topic_sub_rgb):
            rgb = msg.decode().split(',')
            self.rgbw[0] = int(rgb[0])
            self.rgbw[1] = int(rgb[1])
            self.rgbw[2] = int(rgb[2])

        # odebrano wiadomość z wartością bieli
        elif (topic == self.topic_sub_white):
            self.rgbw[3] = int(msg)

        # odebrano wiadomość z efektem
        elif (topic == self.topic_sub_effect):
            self.effect = msg

        # # wyłączenie światła gdy jasność ustawiona na 0
        # if (self.brightness == 0):
        #     self.status = b'OFF'
        #     self.brightness = 20

        self.update_states()  # aktualizacja stanów na serwerze
        # self.set_pwm()                            # ustawienie wartości PWM

    # funkcja aktualizująca dane na serwerze
    def update_states(self):
        # przygotowanie danych
        availability_val = b'online'
        status_val = self.status
        effect_val = self.effect
        brightness_val = bytes(str(self.brightness), 'utf-8')
        rgb_val = bytes(str(self.rgbw[0]) + ',' + str(self.rgbw[1]) + ',' + str(self.rgbw[2]), 'utf-8')
        white_val = bytes(str(self.rgbw[3]), 'utf-8')

        # wysłanie danych
        self.client.publish(self.topic_pub_availability, availability_val)
        self.client.publish(self.topic_pub_brightness, brightness_val)
        self.client.publish(self.topic_pub_rgb, rgb_val)
        self.client.publish(self.topic_pub_white, white_val)
        self.client.publish(self.topic_pub_effect, effect_val)
        self.client.publish(self.topic_pub_state, status_val)

    # funkcja włączająca i wyłączająca efekty - światło
    def let_there_be_light(self):
        if (self.status == b'ON'):
            if (self.effect == b'solid'):
                self.__effect_solid(5, self.brightness)
            elif (self.effect == b'fade'):
                self.__effect_fade(10, 1000)
            elif (self.effect == b'all_colors'):
                self.__effect_all_colors(10, 720, self.brightness)
        else:
            if(self.effect == b'all_colors'):
                self.__effect_all_colors(10, 720, 0)
            else:
                self.__effect_solid(4, 0)
                self.counter = 0

    # funkcja ustawiająca wartości pwm dla kanałów r,g,b (h: 0-360, s,v: 0-1)
    def set_pwm_hsv(self, h, s, v):
        rgb = self.__hsv2rgb(h, s, v)
        self.pwm_R.duty(rgb[0])
        self.pwm_G.duty(rgb[1])
        self.pwm_B.duty(rgb[2])

    # funkcja ustawiająca wartości pwm dla kanałów r,g,b (rgbw: 0-255, brightness: 0-1000)
    def set_pwm_rgb(self, r, g, b, w, brightness):
        self.pwm_R.duty(int((r << 2) * (brightness / 1000)))
        self.pwm_G.duty(int((g << 2) * (brightness / 1000)))
        self.pwm_B.duty(int((b << 2) * (brightness / 1000)))
        self.pwm_W.duty(int((w << 2) * (brightness / 1000)))
        print(self.pwm_R.duty(), self.pwm_G.duty(), self.pwm_B.duty(), self.pwm_W.duty())

    # efekt - stały kolor i jasność światła - płynna zmiana jasności
    def __effect_solid(self, step_time, brightness=0, step=1):
        current_time_ms = ticks_ms()
        if (abs(current_time_ms - self.last_time_ms) > step_time):
            self.last_time_ms = current_time_ms

            current_brightness = brightness * 10
            if (self.last_brightness < current_brightness):
                self.last_brightness += step
                if (self.last_brightness > 1000): self.last_brightness = 1000
            elif (self.last_brightness > current_brightness):
                self.last_brightness -= step
                if (self.last_brightness < 1): self.last_brightness = 0

            self.set_pwm_rgb(self.rgbw[0], self.rgbw[1], self.rgbw[2], self.rgbw[3], self.last_brightness)

    # efekt - przygasanie i rozjaśnianie koloru
    def __effect_fade(self, step_time, steps):
        current_time_ms = ticks_ms()
        if (abs(current_time_ms - self.last_time_ms) > step_time):
            self.last_time_ms = current_time_ms

            if (self.counter < steps):
                self.last_brightness = int(self.counter * 1000 / steps)
                self.set_pwm_rgb(self.rgbw[0], self.rgbw[1], self.rgbw[2], 0, self.last_brightness)
                self.counter += 1
            elif (self.counter >= steps and self.counter < steps * 2):
                self.last_brightness = int((steps * 2 - self.counter) * 1000 / steps)
                self.set_pwm_rgb(self.rgbw[0], self.rgbw[1], self.rgbw[2], 0, self.last_brightness)
                self.counter += 1
            else:
                self.counter = 0

    # efekt - płynna zmiana kolorów
    def __effect_all_colors(self, step_time, steps, brightness=0):
        current_time_ms = ticks_ms()
        if (abs(current_time_ms - self.last_time_ms) > step_time):
            self.last_time_ms = current_time_ms

            if (self.counter < steps):

                current_brightness = brightness*10
                if (self.last_brightness < current_brightness):
                    self.last_brightness += 4
                    if (self.last_brightness > 1000): self.last_brightness = 1000
                elif (self.last_brightness > current_brightness):
                    self.last_brightness -= 4
                    if (self.last_brightness < 1): self.last_brightness = 0

                self.set_pwm_hsv(self.counter * 360 / steps, 1, self.last_brightness / 1000)
                self.counter += 1
            else:
                self.counter = 0

    # funkcja konwertująca kolor hsv do rgb (h: 0-360, s,v: 0-1)
    def __hsv2rgb(self, h, s, v):
        h = float(h)
        s = float(s)
        v = float(v)
        h60 = h / 60.0
        h60f = math.floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0:
            r, g, b = v, t, p
        elif hi == 1:
            r, g, b = q, v, p
        elif hi == 2:
            r, g, b = p, v, t
        elif hi == 3:
            r, g, b = p, q, v
        elif hi == 4:
            r, g, b = t, p, v
        elif hi == 5:
            r, g, b = v, p, q
        r, g, b = int(r * 1023), int(g * 1023), int(b * 1023)
        return r, g, b
