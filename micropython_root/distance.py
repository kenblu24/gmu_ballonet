# This file contains the distance_sensor class
# class distance_sensor gives a tilt-corrected height measurement

import math


class height_lidar:
    def __init__(self, accelerometer, VL53L0X):
        self.accelerometer = accelerometer
        self.vl53l0x = VL53L0X
        self.vl53l0x.set_Vcsel_pulse_period(self.vl53l0x.vcsel_period_type[0], 18)
        self.vl53l0x.set_Vcsel_pulse_period(self.vl53l0x.vcsel_period_type[1], 14)

    def read(self):
        self.vl53l0x.start()
        raw_distance = self.vl53l0x.read()
        self.vl53l0x.stop()
        v = self.accelerometer.getAxes()
        dot_product = -1.0 * v['z']
        v_magnitude = (v['x']**2 + v['y']**2 + v['z']**2)**0.5
        theta = math.acos(dot_product / v_magnitude)
        distance = raw_distance * math.cos(theta)
        return distance


def main():
    global read
    global this
    from machine import Pin, I2C
    import adxl345
    import VL53L0X
    import accelerometer
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    adxl = adxl345.ADXL345(i2c, 83)
    a = accelerometer.accelerometer(adxl, 'adxl345_calibration_2point')
    lidar = VL53L0X.VL53L0X(i2c, 41)
    this = height_lidar(a, lidar)
    read = this.read


if __name__ == "__main__":
    main()
