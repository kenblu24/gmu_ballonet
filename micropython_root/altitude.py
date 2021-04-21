"""
The ALTITUDE class uses a ToF ranger and barometer to calculate the altitude relative to a floor surface.

This class uses a short-range distance measuring device to calculate the height above the floor.
This is then used to offset calculations from a barometer, which measures absolute height compared to sea level.
The output is given as height above the floor in meters.

To use this class, initialize it with a BMP388 device handler, and a ranging device handler.
Then, call find_floor_from_range(set_floor=True) with the floor in range of the ToF ranger.

"""

from time import sleep
from statistics_tools import mean

def mean(m):  # polyfill because Micropython has no module 'statistics'
    return sum(m) / len(m)


class ALTITUDE:
    def __init__(self, barometer, distance):
        self.barometer = barometer
        self.distance = distance
        self.floor_altitude = 0  # On init, altitude will be reported compared to sea level

    # find floor altitude compared to sea level using distance device (ToF sensor)
    def find_floor_from_range(self, n_average=10, set_floor=False):
        # take n measurements to be averaged
        measurements = {'range': [], 'raw_altitude': []}
        for i in range(n_average):
            measurements['raw_altitude'].append(self.barometer.altitude)
            measurements['range'].append(self.distance.read())  # returns mm
            sleep(0.1)
        avg_range_meters = mean(measurements['range']) / 1000.0  # avg and convert to meters
        avg_altitude = mean(measurements['raw_altitude'])
        print("We are {r:.2f}m above the floor".format(r=avg_range_meters))
        print("We are {h:.2f}m compared to sea level".format(h=avg_altitude))
        floor_altitude = avg_altitude - avg_range_meters
        if set_floor:
            self.floor_altitude = floor_altitude
        return floor_altitude

    # Sets current device position as the floor; does not use ToF ranging
    def set_position_as_floor(self, n_average=10):
        measurements = {'raw_altitude': []}
        for i in range(n_average):
            measurements['raw_altitude'].append(self.barometer.altitude)
            sleep(0.2)
        self.floor_altitude = mean(measurements['raw_altitude'])
        return self.floor_altitude

    def get_altitude(self):
        return self.barometer.altitude - self.floor_altitude

    @property
    def meters(self):
        return self.get_altitude()

    # Demo function. Prints average of five samples approximately every second
    def acquire_data(self, readings=20):
        for i in range(readings):
            # altitude = mean([self.get_altitude() for i in range(10)])
            altitude_sum = 0
            n = 5
            for j in range(n):
                altitude_sum += self.get_altitude()
                sleep(0.2)
            altitude = altitude_sum / n
            string = "Altitude :\t {alt:.2f}"
            print(string.format(alt=altitude))  # optional


def main():
    global this
    global acquire_data
    global get_altitude
    global find_floor_from_range
    global set_position_as_floor
    from bmp388 import BMP388
    from VL53L0X import VL53L0X
    from adxl345 import ADXL345
    from accelerometer import ACCELEROMETER
    from distance import HEIGHT_LIDAR

    # I2C Object
    if 'i2c' not in globals():
        from machine import I2C, Pin
        i2c = I2C(0, scl=Pin(22), sda=Pin(21))

    adxl = ADXL345(i2c, 83)
    accelerometer = ACCELEROMETER(adxl, 'adxl345_calibration_2point')
    lidar = VL53L0X(i2c, 41)
    distance_fusion = HEIGHT_LIDAR(accelerometer, lidar)
    barometer = BMP388(i2c)

    this = ALTITUDE(barometer, distance_fusion)
    this.distance.offset = -40.0

    acquire_data = this.acquire_data
    get_altitude = this.get_altitude
    find_floor_from_range = this.find_floor_from_range
    set_position_as_floor = this.set_position_as_floor
