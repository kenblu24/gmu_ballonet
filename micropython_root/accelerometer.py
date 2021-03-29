GRAVITY = 9.80665


class ACCELEROMETER:
    def __init__(self, adxl345, file, unit=GRAVITY):
        self.unit = unit
        self.adxl345 = adxl345
        self.file = file
        self.axes_bi = {e: None for e in {'x', 'y', 'z'}}
        self.axes_bi = (self.axes_bi.copy(), self.axes_bi.copy())
        contents = []
        with open(self.file, "r") as f:
            while True:
                line = f.readline()
                if line:
                    split = line.rstrip().split("\t")
                    contents.extend(split[1:len(split)])
                else:
                    break
        self.axes_bi[0]['x'] = contents[0]
        self.axes_bi[1]['x'] = contents[3]
        self.axes_bi[0]['y'] = contents[7]
        self.axes_bi[1]['y'] = contents[10]
        self.axes_bi[0]['z'] = contents[14]
        self.axes_bi[1]['z'] = contents[17]

    def getAxes(self):
        axes = self.adxl345.getAxes()
        global a_d
        global a_a
        for d in axes:
            a_d = d
            a_a = self.axes_bi
            axes[d] = linear_approximation(
                float(self.axes_bi[0][d]),
                -self.unit,
                float(self.axes_bi[1][d]),
                self.unit,
                axes[d])
        return axes


def linear_approximation(x1, y1, x2, y2, p):
    m = (y2 - y1) / (x2 - x1)
    return m * (p - x1) + y1


def main():
    global getAxes
    global this
    from machine import Pin, I2C
    import adxl345
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    a = adxl345.ADXL345(i2c, 83)
    this = ACCELEROMETER(a, 'adxl345_calibration_2point')
    getAxes = this.getAxes


if __name__ == "__main__":
    main()
