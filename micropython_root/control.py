"""
Authors: Kevin Eckert

General Control File for Sensor Test
This is simply a script that allows one to get data
from the BMP388 sensor and see it printed on screen,
as well as access more detailed, stored information
which is place in a CSV formatted txt file.
"""

from time import sleep
from machine import I2C, Pin
from write import write_data

import BMP388 as BMP
import VL53L0X as L0X  # that's a zero
import adxl345 as ADX  # that's a 1, not an L
import accelerometer as ACCEL
from distance import height_lidar


def acquire_data(seconds=20):
    # Constants and things
    bmp_file = "bmpdata.txt"
    lidar_file = "lidardata.txt"

    # I2C Object
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))

    # Configure BMP
    BMP.set_oversampling(i2c)
    cal = BMP.read_coefficients(i2c)

    # Configure VL50LOX

    adxl = ADX.ADXL345(i2c, 83)
    a = ACCEL.accelerometer(adxl, 'adxl345_calibration_2point')
    lidar = L0X.VL53L0X(i2c, 41)
    this = height_lidar(a, lidar)

    # main loop:
    for i in range(seconds):
        # BMP
        BMPdata = BMP.get_altitude(i2c, cal)
        write_data(bmp_file, str(BMPdata[0]) + "," + str(BMPdata[1]) + "," + str(BMPdata[2]) + "," + str(BMPdata[3]))
        print("BMP " + str(i) + '>\t' + str(BMPdata[0]))  # optional

        # LIDAR

        LIDARdata = str(this.read)
        write_data(lidar_file, LIDARdata)
        print("LDR " + str(i) + '>\t' + LIDARdata)

        sleep(1)

    # Successful Completion Here
    return 1
