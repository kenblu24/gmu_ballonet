"""
Authors: Kevin Eckert

This sets up the webREPL for the ESP32 on boot. 
"""

import network
import webrepl

ap = network.WLAN(network.AP_IF)
ap.config(essid="ESP-AP")
ap.config(max_clients=2)
ap.active(True)

webrepl.start(password="gmuece493")