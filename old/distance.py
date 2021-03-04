measure = None


class VL53L0:
    def __init__(self, i2c, address=41):
        self.i2c = i2c
        self.address = address

    def measure(self):
        pass


def main():
    global measure
    from machine import Pin, I2C
    i2c = I2C(scl=Pin(22), sda=Pin(21))  # must specify pins for some reason
    this = VL53L0(i2c)
    measure = this.measure


if __name__ == '__main__':
    main()
