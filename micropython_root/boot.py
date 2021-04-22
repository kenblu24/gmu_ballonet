# This file is executed on every boot (including wake-boot from deepsleep)
import gc
from sys import modules
from machine import Pin, I2C
# import esp
# esp.osdebug(none)
# import webrepl
# webrepl.start()

i2c = I2C(0, scl=Pin(22), sda=Pin(21))


# You can only import a file once
# Use this to run it a second time (or more)
def reload(mod):
    mod_name = mod.__name__
    del modules[mod_name]
    gc.collect()
    return __import__(mod_name)


# Starts access point, allowing for wireless terminal access
# Connect using SSID and password, then use Webrepl client
# Further information at bottom of page:
# https://docs.micropython.org/en/latest/esp32/quickref.html
def start_ap():
    import network
    import webrepl

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="Blimpy_McBallonetFace",
              password="gmuece493",
              authmode=network.AUTH_WPA_WPA2_PSK
              )
    ap.config(max_clients=2)

    webrepl.start(password="ffff")


start_ap()
