"""
The ALTITUDE class uses up to two distance ranging devices and barometer to calculate the altitude relative to a floor surface.

This class uses the best available distance measuring device to calculate the height above the floor.
This is then used to offset calculations from a barometer
  which measures absolute height compared to sea level.
The output is given as height above the floor in meters.

A barometer is required for this class to function,
  but you can choose not to use it by setting `barometer_drift` high.

To use this class, initialize it
  with a BMP388 device driver object, and a up to two ranging device drivers.

Then, call find_floor_from_range(set_floor=True)
  with the floor in range of the short-range ToF ranger, and hold as steady as possible.
  At least 30 mm (3 cm, or more than an inch) from the floor is good.

"""

from time import sleep
from statistics_tools import mean
from distance import OUT_OF_RANGE


class ALTITUDE:
    def __init__(self, barometer, short_range_finder=None, long_range_finder=None):
        self.barometer = barometer
        self.sr = short_range_finder
        self.lr = long_range_finder
        self.original_floor_altitude = 0  # this should only be set explicitly.
        self.floor_altitude = 0  # On init, altitude will be reported compared to sea level
        # Maximum deviation from known floor altitude. Deviation higher
        # than this will not allow self-calibration
        self.calibration_drift = 0  # set to 0 to disable continual calibration
        # maximum deviation for use of rangefinder
        # Used to prevent rangefinder from being used if object passes below us.
        # Set to very high value to never use barometer.
        self.barometer_drift = 1

    # find floor altitude compared to sea level using shortrange device (ToF sensor)
    def find_floor_from_range(self, n_average=10, set_floor=False):
        # take n measurements to be averaged
        measurements = {'range': [], 'raw_altitude': []}
        for i in range(n_average):
            measurements['raw_altitude'].append(self.barometer.altitude)
            measurements['range'].append(self.sr.read())  # returns mm
            sleep(0.1)
        avg_range_meters = mean(measurements['range']) / 1000.0  # avg and convert to meters
        avg_altitude = mean(measurements['raw_altitude'])
        print("We are {r:.2f}m above the floor".format(r=avg_range_meters))
        print("We are {h:.2f}m compared to sea level".format(h=avg_altitude))
        floor_altitude = avg_altitude - avg_range_meters
        if set_floor:
            self.floor_altitude = floor_altitude
            self.original_floor_altitude = floor_altitude
            print("Floor altitude was set to " + str(floor_altitude))
        return floor_altitude

    # Sets current device position as the floor; does not use ToF ranging
    def set_position_as_floor(self, n_average=5, delay=0.5, offset=0):
        measurements = {'raw_altitude': []}
        for i in range(n_average):
            measurements['raw_altitude'].append(self.barometer.altitude)
            sleep(delay)
        floor_altitude = mean(measurements['raw_altitude']) + offset
        self.original_floor_altitude = floor_altitude
        self.floor_altitude = floor_altitude
        return floor_altitude

    def get_altitude(self):
        # read barometer
        raw_altitude = self.barometer.altitude
        barometer_altitude_rel = raw_altitude - self.floor_altitude
        if self.sr:
            # try reading short-range rangefinder and convert mm to meters.
            distance = self.sr.read() / 1000
            if not 0 < distance < OUT_OF_RANGE:
                distance = None
        if self.lr and not distance:
            # short-range rangefinder didn't work.
            # try reading long-range rangefinder and convert mm to meters.
            distance = self.lr.read() / 1000
            if not 0 < distance < OUT_OF_RANGE:
                distance = None
        if not distance:
            # neither rangefinder got a valid reading. Gotta use barometer.
            return barometer_altitude_rel
        # deviation is the difference in the height above the floor
        # between the barometer and rangefinder reading.
        # When in doubt, we want take the barometer as the truth.
        deviation = abs(distance - barometer_altitude_rel)
        # if rangefinder agrees with barometer, use rangefinder
        if deviation < self.barometer_drift:
            if deviation < self.calibration_drift:
                self.floor_altitude = raw_altitude - distance
            return distance
        # else use barometer
        return barometer_altitude_rel

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
    from distance import HeightTiltCompensator

    # I2C Object
    if 'i2c' not in globals():
        from machine import I2C, Pin
        i2c = I2C(0, scl=Pin(22), sda=Pin(21))

    adxl = ADXL345(i2c, 83)
    accelerometer = ACCELEROMETER(adxl, 'adxl345_calibration_2point')
    tof = VL53L0X(i2c, 41)
    distance_fusion = HeightTiltCompensator(accelerometer, tof)
    barometer = BMP388(i2c)

    this = ALTITUDE(barometer, distance_fusion)
    this.sr.offset = -40.0

    acquire_data = this.acquire_data
    get_altitude = this.get_altitude
    find_floor_from_range = this.find_floor_from_range
    set_position_as_floor = this.set_position_as_floor
