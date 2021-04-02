""" Author(s): Kevin Eckert, Austin Mulville
MaxSONAR Sensor Control
Hardware: MaxSONAR EZ Series Ultrasonic Sensors

Good documentation (as opposed to the official docs, though even this has some wrong stuff):
https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/uart

Notes:
	RX pin should be held high when output from 
	maxsonar sensor is desired. TX pin will then 
	transmit continuously in a specified format,
	starting with 'R' (0101 0010) and ending with 
	carriage return (0000 1101). 
	
	Baudrate  = 9600
	Data Size = 8 bits
	Parity 	  =	none
	Stop bits = 1
	
	timeout and timeout_char need to be fairly large
	
Output Format:
	After the R, each ASCII encoded value corresponds 
	to the centimeters. There is no need to convert 
	to binary. E.g.,
		b'\xf8R100\r'
	means 100 centimeters. 

"""

from machine import Pin, UART
from struct import unpack
from time import sleep

def get_range(sonar):
	data = b''
	data = sonar.read()
	data = str(data)
	data = int(data[7]+data[8]+data[9])
	return data

#uart = UART(2, baudrate=9600, bits=8, parity=None, stop=1, rx=16, tx=17, invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)
uart = UART(2, baudrate=9600, bits=8, parity=None, stop=1, rx=12, tx=13, invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)

print(get_range(uart))