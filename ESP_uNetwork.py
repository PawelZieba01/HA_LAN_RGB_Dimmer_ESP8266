import json
import network
import socket
from uselect import select
from time import sleep

class ESP_uNetwork:
    
    def __init__(self, config_file_dir = ""):
        #jeżeli istnieje plik konfiguracyjny to pobierz dane konfiguracyjne sieci
        if(config_file_dir):

            print("Opening config file: 'conf.json'")

            f = open(config_file_dir, "r")
            config_json = f.read()                          # pobranie danych konfiguracyjnych z pliku config.json
            config_dict = json.loads(config_json)          # zdekodowanie danych json - zamiana na dictionary
            f.close()
            del config_json

            #konfiguracja sieci z pliku
            self.static_ip = config_dict["static_ip"]
            self.mask_ip = config_dict["mask_ip"]
            self.gate_ip = config_dict["gate_ip"]
            self.dns_ip = config_dict["dns_ip"]
            self.ssid = config_dict["ssid"]
            self.password = config_dict["password"]

            del config_dict
            print("Config from file saved..")


    #ręczna konfiguracja sieci
    def set_net_config(self, ssid, password, static_ip, gate_ip, mask_ip="255.255.255.0", dns_ip="8.8.8.8"):
        self.ssid = ssid
        self.password = password
        self.static_ip = static_ip
        self.gate_ip = gate_ip
        self.mask_ip = mask_ip
        self.dns_ip = dns_ip


    #połącz z punktem dostępowym
    def connect_to_AP(self):
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        if not sta_if.isconnected():

            print("Connecting with " + self.ssid +"...")

            sta_if.connect(self.ssid, self.password)
            while not sta_if.isconnected():
                print(".")
                sleep(0.2)
        sta_if.ifconfig((self.static_ip, self.mask_ip, self.gate_ip, self.dns_ip))

        print("WLAN config:", sta_if.ifconfig())


    #nasłuchiwanie zapytań http
    def set_server_listening(self, addr="", port=80):
        self.s = socket.socket()
        if(not addr):
            addr = self.static_ip

        self.s.bind((addr, port))
        self.s.listen(1)
        

    #funkcja odbierająca połączenia z timeoutem
    def get_request(self, handler_fun, timeout=1):
        r, w, err = select((self.s,), (), (), timeout)
        if r:
            for readable in r:
                conn, addr = self.s.accept()
                try:
                    handler_fun(conn, addr)
                except OSError as e:
                    pass











