# This file is executed on every boot (including wake-boot from deepsleep)
import gc
from sys import modules
from machine import Pin, I2C
# import esp
# esp.osdebug(none)
# import webrepl
# webrepl.start()


def start_ap():
    import network
    import webrepl

    wlan = network.WLAN(network.STA_IF)  # create station interface
    wlan.active(True)       # activate the interface
    wlan.scan()             # scan for access points
    wlan.isconnected()      # check if the station is connected to an AP
    wlan.connect('Helium', '#algorithmicBEETROOT')  # connect to an AP
    wlan.config('mac')      # get the interface's MAC address
    wlan.ifconfig()         # get the interface's IP/netmask/gw/DNS addresses

    ap = network.WLAN(network.AP_IF)  # create access-point interface
    ap.config(essid='NSA_Surveilance_Van')  # set the ESSID of the access point
    ap.config(max_clients=3)  # set how many clients can connect to the network
    ap.active(True)         # activate the interface

    webrepl.start()


def reload(mod):
    mod_name = mod.__name__
    del modules[mod_name]
    gc.collect()
    return __import__(mod_name)


def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('Helium', '#algorithmicBEETROOT')
        i = 0
        while not wlan.isconnected():
            if i > 5:
                i = i + 1
                return
    print('network config:', wlan.ifconfig())


# do_connect()
# start_ap()

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
