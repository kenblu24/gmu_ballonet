"""
This class implements the BMP388 barometer and temperature sensor for the ESP32 over i2c.

Authors: Kevin Eckert

Initialize with BMP388(i2c, address)
Get altitude with this.altitude

"""

from time import sleep
from micropython import const  # I don't think I need this
from struct import unpack

# Create BMP388 ID and ADDRESS.
# Note that the SDO pin can be changed, so the address can change during operation if desired.
BMP388_ID = const(0x50)
DEFAULT_SAMPLING = b'\x0D'  # 0000 1101--32x pressure sampling, 2x temp sampling
SEA_LEVEL = 1013.25
FORCE_MEASURE = b'\x13'
RDY = const(0x60)
# REGISTERS
REG_ID = const(0x00)
REG_ERROR = const(0x02)
REG_STATUS = const(0x03)
REG_PRESSUREDATA = const(0x04)  # pressure data contained on registers x04-06
REG_TEMPDATA = const(0x07)  # temp data on reg x07-09
REG_SENSORTIME = const(0x0C)  # from xC-xE
REG_EVENT = const(0x10)
REG_INT_STATUS = const(0x11)
REG_FIFO_LENGTH = const(0x12)  # x12 - x13
REG_FIFO_DATA = const(0x14)
REG_FIFO_WATERMARK = const(0x15)  # x15-x16
REG_FIFO_CONFIG_1 = const(0x17)
REG_FIFO_CONFIG_2 = const(0x18)
REG_INT_CTRL = const(0x19)
REG_IF_CONF = const(0x1A)
REG_CONTROL = const(0x1B)
REG_OSR = const(0x1C)
REG_ODR = const(0x1D)
REG_CONFIG = const(0x1F)
REG_CAL_DATA = const(0x31)  # calibration data actually starts at 0x30, however only 0x31-0x45 are used
REG_CMD = const(0x7E)


class BMP388:
    def __init__(self, i2c, address=0x77):
        self.address = address  # 0x76 if SDO is connected to ground, else 0x77
        self.i2c = i2c
        self._oversampling = None
        self.oversampling = DEFAULT_SAMPLING
        self.cal = self.read_coefficients()
        self.sea_level = SEA_LEVEL

    def get_data(self):
        # Perform one measurement in forced mode
        self.i2c.writeto_mem(self.address, REG_CONTROL, FORCE_MEASURE)

        # Ensure data is ready to read
        while unpack("B", self.i2c.readfrom_mem(self.address, REG_STATUS, 1))[0] & 0x60 != 0x60:
            sleep(0.02)

        data = self.i2c.readfrom_mem(self.address, REG_PRESSUREDATA, 6)

        adc_p = data[2] << 16 | data[1] << 8 | data[0]
        adc_t = data[5] << 16 | data[4] << 8 | data[3]

        # Compensation calculations. temp = temperature
        pd1 = adc_t - self.cal[0]
        pd2 = pd1 * self.cal[1]
        temp = pd2 + (pd1 * pd1) * self.cal[2]

        # Calculate pressure (sec 9.3):
        pd1 = self.cal[8] * temp
        pd2 = self.cal[9] * temp ** 2.0
        pd3 = self.cal[10] * temp ** 3.0
        po1 = self.cal[7] + pd1 + pd2 + pd3

        pd1 = self.cal[4] * temp
        pd2 = self.cal[5] * temp ** 2.0
        pd3 = self.cal[6] * temp ** 3.0
        po2 = adc_p * (self.cal[3] + pd1 + pd2 + pd3)

        pd1 = adc_p ** 2.0
        pd2 = self.cal[11] + self.cal[12] * temp
        pd3 = pd1 * pd2
        po3 = pd3 + self.cal[13] * adc_p ** 3.0

        pressure = po1 + po2 + po3

        # Calculate altitude:
        # see https://www.weather.gov/media/epz/wxcalc/pressureAltitude.pdf
        # The BMP388 provides pressure in Pascals. The elevation formula requires mbar. The conversion is:
        # 1 mbar = 100 Pa. Hence why we divide by 100 in the equation
        return ((44307.7 * (1 - ((pressure / (100 * self.sea_level)) ** 0.190284))), pressure, temp, temp * 9 / 5 + 32)

    @property
    def altitude(self):  # return altitude in meters above sea level
        return self.get_data()[0]

    @property
    def oversampling(self):
        return self._oversampling

    @oversampling.setter
    def oversampling(self, sampling):
        self.i2c.writeto_mem(self.address, REG_OSR, sampling)
        if self.i2c.readfrom_mem(self.address, REG_OSR, 1) != sampling:
            raise IOError("Could not successfully set oversampling")
        self._oversampling = sampling

    def read_coefficients(self):

        coeff = self.i2c.readfrom_mem(self.address, REG_CAL_DATA, 21)
        coeff = unpack("<HHbhhbbHHbbhbb", coeff)  # https://docs.python.org/3/library/struct.html

        calibration = (
            # Convert using formula in section 9.1 of datasheet.
            coeff[0] / 2 ** -8.0,  # T1
            coeff[1] / 2 ** 30.0,  # T2
            coeff[2] / 2 ** 48.0,  # T3
            (coeff[3] - 2 ** 14.0) / 2 ** 20.0,  # P1
            (coeff[4] - 2 ** 14.0) / 2 ** 29.0,  # P2
            coeff[5] / 2 ** 32.0,  # P3
            coeff[6] / 2 ** 37.0,  # P4
            coeff[7] / 2 ** -3.0,  # P5
            coeff[8] / 2 ** 6.0,  # P6
            coeff[9] / 2 ** 8.0,  # P7
            coeff[10] / 2 ** 15.0,  # P8
            coeff[11] / 2 ** 48.0,  # P9
            coeff[12] / 2 ** 48.0,  # P10
            coeff[13] / 2 ** 65.0  # P11
        )
        return calibration
