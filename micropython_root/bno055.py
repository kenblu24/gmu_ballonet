"""Authors: Kevin Eckert
Simple library for use with Adafruit BNO055

USAGE EXAMPLE (using quaternion):
	velocity = 0
	delta = 0.6
	set_mode(i2c,address,mode=12)
	sleep(1)	#to allow mode change
	matrix = get_quaternion_data(i2c,address)
	accel = get_linear_accel_data(i2c,address)
	accel = quaternion_rotation(matrix,accel)
	sleep(delta)
	velocity = calculate_velocity(velocity,accel,delta)
	
USAGE EXAMPLE (using grav vector to form rotation matrix):
	velocity = 0
	delta = 0.6
	set_mode(i2c,address,mode=12)
	sleep(1)
	grav_accel = get_grav_accel_data(i2c,address)
	accel = get_linear_accel_data(i2c,address)
	matrix = grav_vector_rotation_correction_matrix(grav)
	accel = get_adjusted_accel(matrix, accel)
	sleep(delta)
	velocity = calculate_velocity(velocity,accel,delta)

The BNO055 performs best when external crystal is used.
Configure settings, then set mode. It takes 7ms to switch
from configuration mode to other modes, and 19ms to switch
back to config mode. 

Pitch and yaw data is used to calculate orientation
Fusion mode is necessary to differentiate gravity and movement acceleration

Consider configuring self-test option (p47)

Note: the sensor must be calibrated before use (pg48)

In fusion mode, we can get linear acceleration directly, which 
is acceleration already compensating for gravity.

Note: struct.unpack() and I2C.readfrom_mem()
	Suppose you pass an argument like:
		data = i2c.readfrom_mem(addr,reg,n)
	Now you want to unpack it with struct:
		array = unpack("BBBBB...", data)
	And you wonder what does array[0] correspond to?
	The answer is that array[0] corresponds to the 
	leftmost element of the string argument of unpack,
	which in turn corresponds to the first data read 
	by the readfrom_mem function (i.e., the data in 
	reg, before you burst read for the n bits your reading)
	This also implies that we should tread the data as 
	little-endian, since the very first bit we read is the 
	least significant bit. 

Helpful Resources: 
	Bosch Driver (in C)
	https://github.com/BoschSensortec/BNO055_driver
	
	Adafruit Circuit Python Libraries
	https://github.com/adafruit/Adafruit_BNO055
	
	Matlab (includes useful advice on calibration)
	https://www.mathworks.com/help/supportpkg/arduino/ref/bno055imusensor.html
	
	Rotation Matrices using gravity vector
	https://www.allaboutcircuits.com/technical-articles/how-to-interpret-IMU-sensor-data-dead-reckoning-rotation-matrix-creation/
"""

from machine import Pin, I2C
from time import sleep
from struct import unpack
import math

#Device i2c default address--actually, it seems like 0x28 might be 
#preferred, sinec when I'm connected via usb I have to use it instead. Hmmm.
address = 0x29#or 0x28, when set to alternative mode.
#All 12 configuration modes
config=b'\x00'
acconly=b'\x01'
magonly=b'\x02'
gyroonly=b'\x03'
accmag=b'\x04'
accgyro=b'\x05'
maggyro=b'\x06'
amg=b'\x07'
imu=b'\x08'
compass=b'\x09'
m4g=b'\x0A'
ndof_off=b'\x0B'
ndof=b'\x0C'
#Control Registers:
OPR_REG = 0x3D
UNIT_SEL_REG = 0x3B
AXIS_MAP_REG = 41
AXIS_MAP_SIGN_REG = 42
#Accel Data Registers:
ACC_X_LSB = 0x08
ACC_X_MSB = 0x09
ACC_Y_LSB = 0x0A
ACC_Y_MSB = 0x0B
ACC_Z_LSB = 0x0C
ACC_Z_MSB = 0x0D
#Gravity Vector Data Registers:
GRAV_X_LSB = 0x2E
GRAV_X_MSB = 0x2F
GRAV_Y_LSB = 0x30
GRAV_Y_MSB = 0x31
GRAV_Z_LSB = 0x32
GRAV_Z_MSB = 0x33
#Linear Accel Data Registers:
LIN_ACC_X_LSB = 0x28
LIN_ACC_X_MSB = 0x29
LIN_ACC_Y_LSB = 0x2A
LIN_ACC_Y_MSB = 0x2B
LIN_ACC_Z_LSB = 0x2C
LIN_ACC_Z_MSB = 0x2D
#quaternion Data Registers:
QUAT_W_LSB = 0x20
QUAT_W_MSB = 0x21
QUAT_X_LSB = 0x22
QUAT_X_MSB = 0x23
QUAT_Y_LSB = 0x24
QUAT_Y_MSB = 0x25
QUAT_Z_LSB = 0x26
QUAT_Z_MSB = 0x27
#Euler Angle Data Registers:
EUL_HEADING_LSB = 0x1A
EUL_HEADING_MSB = 0x1B
EUL_ROLL_LSB = 0x1C
EUL_ROLL_MSB = 0x1D
EUL_PITCH_LSB = 0x1E
EUL_PITCH_MSB = 0x1F

"""
Function to create an i2c object.
"""
def make_i2c(scl_pin=22,sda_pin=21):
	i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
	return i2c
	
"""
Configuration Functions: 
set the operating mode to the desired mode. 
p.20 of the datasheet has details.
The other two functions allow you to adjust the axis 
and data format, though they are not necessary to use 
if operating in fusion mode.
"""
def set_mode(i2c, addr=address,mode=12):
	if mode==0:#Configuration Mode
		i2c.writeto_mem(addr,OPR_REG,config)
	elif mode==1:#Non fusion modes
		i2c.writeto_mem(addr,OPR_REG,acconly)
	elif mode==2:
		i2c.writeto_mem(addr,OPR_REG,magonly)
	elif mode==3:
		i2c.writeto_mem(addr,OPR_REG,gyroonly)
	elif mode==4:
		i2c.writeto_mem(addr,OPR_REG,accmag)
	elif mode==5:
		i2c.writeto_mem(addr,OPR_REG,accgyro)
	elif mode==6:
		i2c.writeto_mem(addr,OPR_REG,maggyro)
	elif mode==7:
		i2c.writeto_mem(addr,OPR_REG,amg)
	elif mode==8:#fusion modes
		i2c.writeto_mem(addr,OPR_REG,imu)
	elif mode==9:
		i2c.writeto_mem(addr,OPR_REG,compass)
	elif mode==10:
		i2c.writeto_mem(addr,OPR_REG,m4g)
	elif mode==11:
		i2c.writeto_mem(addr,OPR_REG,ndof_off)
	elif mode==12:
		i2c.writeto_mem(addr,OPR_REG,ndof)
	else:
		return 1
	return i2c.readfrom_mem(addr,OPR_REG,1)
	
def set_data_format(i2c, set_unit_reg):
	i2c.writeto_mem(addr, UNIT_SEL_REG, set_unit_reg)
	return 0
	
def set_axis(i2c, axis_config,sign_config):
	i2c.writeto_mem(addr, AXIS_MAP_REG, axis_config)
	i2c.writeto_mem(addr, AXIS_MAP_SIGN_REG, sign_config)

"""
Acceleration Data Functions
The return an array of numbers which correspond to the 
acceleration measured. In terms of axis, the data is
	[X acceleration,Y accleration,Z acceleration]
For linear acceleration, 100 lsb corresponds to 1 m/s^2
Thus, the output data from these functions is in cm/s^2.
"""	
def get_linear_accel_data(i2c,addr=address):
	data = i2c.readfrom_mem(addr,LIN_ACC_X_LSB,6)
	data = unpack("<hhh", data)
	return data
	
def get_accel_data(i2c,addr=address):
	data = i2c.readfrom_mem(addr,ACC_X_LSB,6)
	data = unpack("<hhh", data)
	return data
	
def get_grav_accel_data(i2c,addr=address):
	data = i2c.readfrom_mem(addr,GRAV_X_LSB,6)
	data = unpack("<hhh", data)
	return data
	
"""
Euler Angle and quaternion Data Functions
The data is formated as follows:
	[heading, roll, pitch], 1 degree = 16 lsb, 1 radian = 900 LSB (euler)
	[W,X,Y,Z] (quaternion), 1 quaternion = 2^14 lsb
Headings are relative to the device's internal axis configuration (p24).
"""
def get_euler_data(i2c,addr=address):
	data = i2c.readfrom_mem(addr,EUL_HEADING_LSB,6)
	data = unpack("<hhh", data)
	return data
	
def get_quaternion_data(i2c,addr=address):
	data = i2c.readfrom_mem(addr,QUAT_W_LSB,8)
	data = unpack("<hhhh", data)
	return data

"""
Angle Manipulation Functions:
This takes us from the IMU reference frame to the inertial reference frame. 
See: 
	A tutorial on euler angles and quaternions, Moti Ben-Ari (Weizmann Institute of Science) 2014
	http://www.chrobotics.com/library/understanding-quaternions#:~:text=Regardless%20of%20whether%20quaternion%20multiplication,vector%2C%20the%20operation%20is%20reversed
The divisor is needed because 1 quaternion unit = 2^14 = 16384, according to the datasheet, p35
This is a little slow, but is still much faster than using trig functions. 
As with the input acceleration, the output here is in cm/s^2
NOTE: Due to datasheet ambiguities, I don't know if I need to use the inverse of the coefficients, or the provided values.
Testing suggests to use the values without inverting them.

The grav_vector_rotation_correction_matrix argument should be a vector of the x, y and z components of the gravity acceleration register. 
It is recommended to generate the matrix only once, and to use it for correction calculations thereafter, since it 
is somewhat expensive computationally, and we want to save clock cycles for the quaternion rotation. 
Output is of the form
	[x,y,z]
	
The get_adjusted_accel arguments should be the matrix output of the correction_matrix function, and any acceleration vector.
The function simply performs matrix multiplication, using the matrix argument as the rotation matrix, and the accel argument 
as the vector to be rotated. 
"""
def quaternion_rotation(quaternion,accel):
	divisor = 16384
	#q = [quaternion[0]/divisor, -quaternion[1]/divisor, -quaternion[2]/divisor, -quaternion[3]/divisor]
	q = [quaternion[0]/divisor, quaternion[1]/divisor, quaternion[2]/divisor, quaternion[3]/divisor]
	new_accel_vector = \
		[accel[0]*(q[0]**2 + q[1]**2 - q[2]**2 - q[3]**2) + 2*accel[1]*(q[1]*q[2] - q[0]*q[3]) + 2*accel[2]*(q[0]*q[2] + q[1]*q[3]) ,\
		2*accel[0]*(q[0]*q[3] + q[1]*q[2]) + accel[1]*(q[0]**2 - q[1]**2 + q[2]**2 - q[3]**2) + 2*accel[2]*(q[2]*q[3] - q[0]*q[1]) ,\
		2*accel[0]*(q[1]*q[3] - q[0]*q[2]) + 2*accel[1]*(q[0]*q[1] + q[2]*q[3]) + accel[2]*(q[0]**2 - q[1]**2 - q[2]**2 + q[3]**2)]
	return new_accel_vector

def grav_vector_rotation_correction_matrix(grav):
	divisor = math.sqrt(grav[0]**2 + grav[1]**2 + grav[2]**2)
	x = grav[0]/divisor
	y = grav[1]/divisor
	z = grav[2]/divisor
	rotation_matrix = [\
			  [(y**2 - z*(x**2))/(x**2 + y**2), (-x*y - x*y*z)/(x**2 + y**2), x],\
			  [(-x*y - x*y*z)/(x**2 + y**2), (x**2 - z*(y**2))/(x**2 + y**2), y],\
			  [-x, -y, -z]\
			  ]
	return rotation_matrix
	
def get_adjusted_accel(matrix, accel):
	output = [0,0,0]
	for i in range(len(matrix)):
		for j in range(len(matrix[i])):
			output[i] += matrix[i][j]*accel[j]
	return output
	

"""
Velocity Calculation Functions:
These functions calculate velocity as 
	v = a*T
where a is the acceleration and T is the sample rate. 
The function takes the current velocity, and adds or 
subtracts the change in velocity from it. Then it returns
the adjusted velocity. 
Sample rate should be in seconds
Velocity should be a 3 element array. The ouput returns in the 
format [X,Y,Z]
"""
def calculate_velocity(velocity, accel, sample_rate):
	v = [velocity[0] + accel[0]*sample_rate,\
		 velocity[1] + accel[1]*sample_rate,\
		 velocity[2] + accel[2]*sample_rate]
	return v
