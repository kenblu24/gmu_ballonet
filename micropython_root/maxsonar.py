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

    The uart device should be configured as follows.
    I emphasize that, if timeout is set too low, the
    device WILL NOT WORK PROPERLY:

    Baudrate  = 9600
    Data Size = 8 bits
    Parity    = none
    Stop bits = 1
    invert    = UART.INV_RX | UART.INV_TX
    timeout   = 100
    timeout_char = 100

    Here is a line for ease of use with the machine UART class. This will work, choose rx and tx pins to flavor:

    # uart = UART(2, baudrate=9600, bits=8, parity=None, stop=1, rx=12, tx=13,
                  invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)

    Note, the timeout does not affect the sample rate.

Output Format:
    After the R, each ASCII encoded value corresponds
    to the centimeters. There is no need to convert
    to binary. E.g.,
        b'\xf8R100\r'
    means 100 centimeters.

"""

from machine import UART
from time import sleep

_IO_TIMEOUT = 6


class XLMaxSonarUART:
    def __init__(self, channel=2, rx=12, tx=13):
        self.DEVICE_TYPE = 'XL-MAXSONAR'
        self._uart = UART(channel, baudrate=9600, bits=8, parity=None, stop=1, rx=rx, tx=tx,
                          invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)

    @property
    def range(self):
        self.start()
        sleep(0.1)
        return self.read()

    def start(self):
        self._uart.write(b'\x01')  # create pulse on TX pin

    def read(self):
        i = 0
        data = b''
        while i < _IO_TIMEOUT:
            data = self._uart.read(1)
            if data == b'R':
                data = self._uart.read(4)[:3]
                return int(data.decode())
            elif data is None:
                self.start()
            i += 1


# uart = UART(2, baudrate=9600, bits=8, parity=None, stop=1, rx=16, tx=17,
#             invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)
# uart = UART(2, baudrate=9600, bits=8, parity=None, stop=1, rx=12, tx=13,
#             invert=UART.INV_RX | UART.INV_TX, timeout=100, timeout_char=100)
# print(get_range(uart))
