# TODO: implement temperature smoothing for thermal runaway protection
from micropython import const
import _thread
from time import sleep
from machine import Pin, I2C
from drv8833 import drv8833
import ntc

_MAX_LIST_SIZE = const(255)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
t1 = ntc.thermometer(i2c, 72, "epcos100k.tsv")

hbridge = drv8833(1000, 32, 33, 25, 26, None, None)
setpoint = 0.0
_T = const(1)
_TIMEOUT_SECONDS = const(30)
_TIMEOUT_CYCLES = int(_TIMEOUT_SECONDS / _T)
starting_temperature = -273.15
enable = False

if _TIMEOUT_CYCLES > 255:
    print("TIMEOUT TOO LONG OR PERIOD TOO SHORT")


def __loop():
    global setpoint
    global starting_temperature
    n = 0
    previous_setpoint = -273.15
    history = []
    cycles_since_start = 0
    while True:
        if not enable:
            return
        temperature = t1.get_temperature()
        if not safe_temperature(temperature):
            hbridge.emergency_stop()
            print("Stopping heat/cool! Unsafe temperature: " + str(temperature))
            _thread.exit()
            return
        if float(setpoint) is not float(previous_setpoint):
            # if setpoint changed
            starting_temperature = temperature
            cycles_since_start = 0
            print("starting temperature: " + str(starting_temperature))
        e = setpoint - temperature
        pwm_duty = e * (1 / 2)
        pwm_duty = min(abs(pwm_duty), 1)
        direction = "Reverse" if e < 0 else "Forward"
        hbridge.power(pwm_duty, direction)

        if cycles_since_start > _TIMEOUT_CYCLES:
            if not abs(e) < 5.0:  # if temperature is not within 5C of setpoint
                delta = 0
                if setpoint > starting_temperature:
                    # if setpoint is higher than starting temperature
                    delta = temperature - starting_temperature
                elif setpoint < starting_temperature:
                    # if setpoint is lower than starting temperature
                    delta = starting_temperature - temperature

                if delta < 1:
                    # if temperature has not moved more than 1C towards setpoint
                    hbridge.emergency_stop()
                    print("Thermal runaway protection activated.")
                    print("Check that thermistor is properly mounted and functioning.")
                    _thread.exit()
                    return
        print("n since: " + str(cycles_since_start)
              + ", set: " + str(setpoint)
              + ", temp: " + str(temperature) + " C")
        #
        fix_push(history, temperature)
        previous_setpoint = setpoint
        n = n + 1
        cycles_since_start += 1
        sleep(_T)


def start(temperature_setpoint):
    global setpoint
    global enable
    global starting_temperature
    global hbridge
    setpoint = float(temperature_setpoint)
    enable = True
    starting_temperature = t1.get_temperature()
    hbridge = drv8833(1000, 32, 33, 25, 26, None, None)
    _thread.start_new_thread(__loop, ())


def safe_temperature(temperature):
    if ((temperature > 50)  # max temperature
            | (temperature < -10)):  # min temperature (thermistor wire broken?)
        return False
    return True


def setpoint(temperature):
    global setpoint
    setpoint = temperature


def fix_push(o, value):
    if len(o) + 1 > _MAX_LIST_SIZE:
        o.pop(0)
    try:
        o.append(value)
    except MemoryError:
        hbridge.emergency_stop()
        raise
