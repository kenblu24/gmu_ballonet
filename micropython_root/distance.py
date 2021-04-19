# This file contains the distance_sensor class
# class distance_sensor gives a tilt-corrected height measurement

import math


class HEIGHT_LIDAR:
    def __init__(self, accelerometer, VL53L0X):
        self.accelerometer = accelerometer
        self.vl53l0x = VL53L0X
        # set long range mode
        self.vl53l0x.set_Vcsel_pulse_period(self.vl53l0x.vcsel_period_type[0], 18)
        self.vl53l0x.set_Vcsel_pulse_period(self.vl53l0x.vcsel_period_type[1], 14)
        self.vl53l0x.set_measurement_timing_budget(33000)  # API broken, this doesn't work
        self.offset = 0  # single-point calibration offset for VL53L0X

    def read(self):
        self.vl53l0x.start()
        self.vl53l0x.read()
        raw_distance = self.vl53l0x.read()
        self.vl53l0x.stop()
        if raw_distance > 8100:  # VL53L0X typically reads 8192 when out of range (too far)
            return float('inf')
        # calibration offset for TOF sensor
        ranged_distance = max(raw_distance + self.offset, 1)
        v = self.accelerometer.getAxes()
        dot_product = -1.0 * v['z']
        v_magnitude = math.sqrt(v['x']**2 + v['y']**2 + v['z']**2)
        theta = math.acos(dot_product / v_magnitude)
        if not 0.0 < theta < math.radians(45):
            return float('-inf')
        cone_correction_factor = 1 - (min(ranged_distance, 2000) / 2000) * 0.5
        distance = ranged_distance * math.cos(theta * cone_correction_factor)
        return distance


def main():
    global read  # make function global
    global this
    from machine import Pin, I2C
    import adxl345
    import VL53L0X
    import accelerometer
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    adxl = adxl345.ADXL345(i2c, 83)
    a = accelerometer.ACCELEROMETER(adxl, 'adxl345_calibration_2point')
    lidar = VL53L0X.VL53L0X(i2c, 41)
    this = HEIGHT_LIDAR(a, lidar)
    this.offset = -50
    read = this.read  # make function callable (so we can call distance.read() )


if __name__ == "__main__":
    main()
