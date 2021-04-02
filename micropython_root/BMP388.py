"""
Authors: Kevin Eckert

Use this class to configure a BMP 388 Sensor in micropython
It takes a bare minimum approach, to do only what is necessary
to get the highest resolution relative altitude measurements.

"""

from machine import Pin, I2C
from time import sleep
from micropython import const#I don't think I need this
from struct import unpack

#Create BMP388 ID and ADDRESS.
#Note that the SDO pin can be changed, so the address can change during operation if desired.
_BMP388_ID = const(0x50)
_BMP388_ADDRESS = 0x77#0x76 if SDO is connected to ground, else 0x77
_DEFAULT_SAMPLING = b'\x0D'#0000 1101--32x pressure sampling, 2x temp sampling
_SEA_LEVEL = 1013.25
_FORCE_MEASURE = b'\x13'
_RDY = const(0x60)
#REGISTERS
_REG_ID = const(0x00)
_REG_ERROR = const(0x02)
_REG_STATUS = const(0x03)
_REG_PRESSUREDATA = const(0x04)#pressure data contained on registers x04-06
_REG_TEMPDATA = const(0x07)#temp data on reg x07-09
_REG_SENSORTIME = const(0x0C)#from xC-xE 
_REG_EVENT = const(0x10)
_REG_INT_STATUS = const(0x11)
_REG_FIFO_LENGTH = const(0x12)#x12 - x13
_REG_FIFO_DATA = const(0x14)
_REG_FIFO_WATERMARK = const(0x15)#x15-x16
_REG_FIFO_CONFIG_1 = const(0x17)
_REG_FIFO_CONFIG_2 = const(0x18)
_REG_INT_CTRL = const(0x19)
_REG_IF_CONF = const(0x1A)
_REG_CONTROL = const(0x1B)
_REG_OSR = const(0x1C)
_REG_ODR = const(0x1D)
_REG_CONFIG = const(0x1F)
_REG_CAL_DATA = const(0x31)#calibration data actually starts at 0x30, however only 0x31-0x45 are used
_REG_CMD = const(0x7E)



def make_i2c(scl_pin=22, sda_pin=21):
	i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
	return i2c
	
def set_oversampling(i2c, sampling=_DEFAULT_SAMPLING):
	i2c.writeto_mem(_BMP388_ADDRESS, _REG_OSR, sampling)
	if i2c.readfrom_mem(_BMP388_ADDRESS, _REG_OSR, 1) != sampling:
		return 1
		
def read_coefficients(i2c):
	bytes21 = 21

	coeff = i2c.readfrom_mem(_BMP388_ADDRESS, _REG_CAL_DATA, bytes21)
	coeff = unpack("<HHbhhbbHHbbhbb", coeff)#https://docs.python.org/3/library/struct.html

	calibration = (
		#Convert using formula in section 9.1 of datasheet.
		coeff[0] / 2 ** -8.0, #T1
		coeff[1] / 2 ** 30.0, #T2
		coeff[2] / 2 ** 48.0, #T3
		(coeff[3] - 2 ** 14.0) / 2 ** 20.0, #P1
		(coeff[4] - 2 ** 14.0) / 2 ** 29.0, #P2
		coeff[5] / 2 ** 32.0, #P3
		coeff[6] / 2 ** 37.0, #P4
		coeff[7] / 2 ** -3.0, # P5
		coeff[8] / 2 ** 6.0, # P6
		coeff[9] / 2 ** 8.0, # P7
		coeff[10] / 2 ** 15.0, # P8
		coeff[11] / 2 ** 48.0, # P9
		coeff[12] / 2 ** 48.0, # P10
		coeff[13] / 2 ** 65.0 #P11
	)
	return calibration
	
def get_altitude(i2c, cal, sea_level=_SEA_LEVEL):
	bytes6 = 6
	#Perform one measurement in forced mode
	i2c.writeto_mem(_BMP388_ADDRESS, _REG_CONTROL, _FORCE_MEASURE)
	
	#Ensure data is ready to read
	while unpack("B", i2c.readfrom_mem(_BMP388_ADDRESS, _REG_STATUS, 1))[0] & 0x60 != 0x60:
		#print(i2c.readfrom_mem(_BMP388_ADDRESS, _REG_STATUS, 1))
		sleep(0.02)
	
	data = i2c.readfrom_mem(_BMP388_ADDRESS, _REG_PRESSUREDATA, bytes6)
	
	adc_p = data[2]<<16 | data[1]<<8 | data[0]
	adc_t = data[5]<<16 | data[4]<<8 | data[3]
	
	#Compensation calculations. temp = temperature
	pd1 = adc_t - cal[0]
	pd2 = pd1 * cal[1]
	temp = pd2 + (pd1 * pd1) * cal[2]
	
	#Calculate pressure (sec 9.3):
	pd1 = cal[8] * temp
	pd2 = cal[9] * temp ** 2.0
	pd3 = cal[10] * temp ** 3.0
	po1 = cal[7] + pd1 + pd2 + pd3
	
	pd1 = cal[4] * temp
	pd2 = cal[5] * temp ** 2.0
	pd3 = cal[6] * temp ** 3.0
	po2 = adc_p * (cal[3] + pd1 + pd2 + pd3)
	
	pd1 = adc_p ** 2.0
	pd2 = cal[11] + cal[12] * temp
	pd3 = pd1 * pd2
	po3 = pd3 + cal[13] * adc_p ** 3.0
	
	pressure = po1 + po2 + po3
	
	#Calculate altitude:
	#see https://www.weather.gov/media/epz/wxcalc/pressureAltitude.pdf
	#The BMP388 provides pressure in Pascals. The elevation formula requires mbar. The conversion is:
	#1 mbar = 100 Pa. Hence why we divide by 100 in the equation
	return ((44307.7 * (1 - ((pressure/(100*sea_level)) ** 0.190284))), pressure, temp, temp*9/5 + 32)