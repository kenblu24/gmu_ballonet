'''
Height tilt-correction for distance sensors using ADXL345 accelerometer

# class HeightTiltCompensator gives a tilt-corrected height measurement
# Ranging device may be VL53L0X using one of two device drivers
#  or Maxbotix XL-Maxsonar (UART)
# Accelerometer device must be ADXL345
# Uses angle of device compared to gravity vector to compensate height reading
'''

import math

OUT_OF_RANGE = float('inf')
INVALID = float('-inf')


class HeightTiltCompensator:
    def __init__(self, accelerometer, ranging_device):
        self.accelerometer = accelerometer
        self.rangefinder = ranging_device
        self.offset = 0  # single-point calibration offset for ranging device
        # adjustment for cone beam compensation (edges of cone read closer)
        # without it, tilting further will cause compensated height to be low
        self.cone_adjust = 1  # value of 0 disables cone adjustment. 1 is max
        # maximum tilt allowed before distance measurement is marked invalid
        self.max_angle = math.radians(45)

        # set certain constants based on ID string in device driver class.
        try:
            self.type = ranging_device.DEVICE_TYPE
        except AttributeError:
            raise NotImplementedError("Object used for ranging_device has no DEVICE_TYPE.")
        if self.type == 'VL53L0X_ada':
            self.read = self.read_VL53L0X_ada
            self.MAX_RANGE = 1200
            self.MIN_RANGE = 5
            self.CONE_ADJUST = 0.5
        elif self.type == 'VL53L0X_polulu':
            self.read = self.read_VL53L0X_polulu
            self.MAX_RANGE = 2000
            self.MIN_RANGE = 5
            self.CONE_ADJUST = 0.5
            self.rangefinder.set_Vcsel_pulse_period(self.rangefinder.vcsel_period_type[0], 18)
            self.rangefinder.set_Vcsel_pulse_period(self.rangefinder.vcsel_period_type[1], 14)
            self.rangefinder.set_measurement_timing_budget(33000)  # API broken, this doesn't work
        elif self.type == 'XL-MAXSONAR':
            self.read = self.read_XLMAXSONAR
            self.MAX_RANGE = 7500
            self.MIN_RANGE = 200
            self.CONE_ADJUST = 0.8

    # this will be used if device is UART maxsonar type
    def read_XLMAXSONAR(self):
        raw_distance = self.rangefinder.range
        if raw_distance > 7600:
            return OUT_OF_RANGE
        ranged_distance = max(raw_distance + self.offset, 1)
        return self.tilt_compensation(ranged_distance)

    # this will be used if device is serial maxsonar type
    def read_VL53L0X_ada(self):
        raw_distance = self.rangefinder.range
        if raw_distance > 8100:  # VL53L0X typically reads 8192 when out of range (too far)
            return OUT_OF_RANGE
        # calibration offset for TOF sensor
        ranged_distance = max(raw_distance + self.offset, 1)
        return self.tilt_compensation(ranged_distance)

    # this will be used if rangfinder is VL53L0X (polulu driver).
    def read_VL53L0X_polulu(self):
        self.rangefinder.start()
        # driver timings are broken in long-range, so need to call read() twice
        self.rangefinder.read()
        raw_distance = self.rangefinder.read()
        self.rangefinder.stop()
        if raw_distance > 8100:  # VL53L0X typically reads 8192 when out of range (too far)
            return OUT_OF_RANGE
        # calibration offset for TOF sensor
        ranged_distance = max(raw_distance + self.offset, 1)
        return self.tilt_compensation(ranged_distance)    # this will be used if rangfinder is VL53L0X (polulu driver).

    def get_angle_vertical(self):
        v = self.accelerometer.getAxes()
        dot_product = -1.0 * v['z']
        v_magnitude = math.sqrt(v['x']**2 + v['y']**2 + v['z']**2)
        return math.acos(dot_product / v_magnitude)

    def tilt_compensation(self, distance):
        theta = self.get_angle_vertical()
        # return invalid if we're not pointing mostly straight down
        if not 0.0 < theta < self.max_angle:
            return INVALID
        # cone correction scales the effect of tilt compensation with the distance read
        # This may need to be re-written; I don't think my math is right
        cone_correction = 1 - (min(distance, self.MAX_RANGE) / self.MAX_RANGE) * self.CONE_ADJUST
        distance = distance * math.cos(theta * cone_correction)
        return int(distance)


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
    tof = VL53L0X.VL53L0X(i2c, 41)
    this = HeightTiltCompensator(a, tof)
    this.offset = -50
    read = this.read  # make function callable (so we can call distance.read() )


if __name__ == "__main__":
    main()
