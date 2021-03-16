# def do_connect(ssid, pwd):
#     import network
#     from time import sleep
#     sta_if = network.WLAN(network.STA_IF)
#     if not sta_if.isconnected():
#         print("connecting to network...")
#         sta_if.active(True)
#         sta_if.connect(ssid, pwd)
#         while not sta_if.isconnected():
#             print(".")
#             sleep(0.2)
#     sta_if.ifconfig(("192.168.1.45", "255.255.255.0", "192.168.1.1", "8.8.8.8"))
#     print("network config:", sta_if.ifconfig())
#
#
# import esp
# esp.osdebug(None)
#
# print("")
# print("")
# print("")
# #do_connect('bestconnect.pl 130', 'pawel130')
