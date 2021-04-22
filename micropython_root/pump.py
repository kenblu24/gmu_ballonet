from machine import Pin
from drv8833 import DRV8833

# args: pwm_frequency, sleep_pin, fault_pin, in1_pin, in2_pin, in3_pin, in4_pin
hbridge1 = DRV8833(1000, Pin(32), Pin(33), Pin(25), Pin(26), Pin(27), Pin(14))
hbridge2 = DRV8833(1000, Pin(15), Pin(2), Pin(4), Pin(16), Pin(17), Pin(5))


# H-Bridge 1 Motor A: In pump
# H-Bridge 1 Motor B: Out pump

# H-Bridge 2 Motor A: Exhaust valve
#   (NC, check adafruit doc for pneumatic connections)

def pump_in(duty=1):
    hbridge1.motor['A'].duty = duty
    hbridge1.motor['B'].duty = 0
    hbridge2.motor['A'].duty = 0


def pump_out(duty=1):
    hbridge1.motor['A'].duty = 0
    hbridge1.motor['B'].duty = duty
    hbridge2.motor['A'].duty = duty


def stop():
    hbridge1.motor['A'].duty = 0
    hbridge1.motor['B'].duty = 0
    hbridge2.motor['A'].duty = 0


def emergency_stop():
    hbridge1.emergency_stop()
    hbridge2.emergency_stop()
