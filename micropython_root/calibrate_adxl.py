'''
Wizard for procedure to generate calibration data for ADXL345

Read and understand the Adafruit guide here:
https://learn.adafruit.com/adxl345-digital-accelerometer/programming

Then, run `import calibrate_adxl` and follow the prompts.
ADXL should be aligned against a backstop for best results.

Results will be stored in the file designated by `FILENAME`
said file can be fed to our ACCELEROMETER class.

The results will be an average of several readings;
the number of readings is determined by `READINGS`

'''


from time import sleep

READINGS = 5
FILENAME = "adxl345_calibration_2point"


def calibrate(adxl345):
    global a
    global axes_bi
    a = adxl345
    axes_bi = {e: None for e in {'x', 'y', 'z'}}
    for d in axes_bi:
        axes_bi[d] = calibrate_axis(d)
    print("Would you like to save this data to file?")
    print("If so, type 'yes', or anything else to cancel.")
    print("If existing, " + FILENAME + " will be overwritten.")
    p = input("Write to " + FILENAME + "? : ")
    if p is not "yes":
        return
    with open(FILENAME, 'w') as f:
        f.write(axes_string("X negative:", axes_bi['x'][0]))
        f.write(axes_string("X positive:", axes_bi['x'][1]))
        f.write(axes_string("Y negative:", axes_bi['y'][0]))
        f.write(axes_string("Y positive:", axes_bi['y'][1]))
        f.write(axes_string("Z negative:", axes_bi['z'][0]))
        f.write(axes_string("Z positive:", axes_bi['z'][1]))


def axes_string(axis_label, axes):
    return (
        axis_label + "\t{0:+.4f}\t{1:+.4f}\t{2:+.4f}\n"
    ).format(axes['x'], axes['y'], axes['z'])


def calibrate_axis(axis):
    print("Align the " + axis + " arrow towards the ground.")
    print("Press Enter when ready.")
    input()
    axes0 = average_readings(READINGS)
    print(str(axes0))
    print()
    print("Align the " + axis + " arrow away from the ground.")
    print("Press Enter when ready.")
    input()
    axes1 = average_readings(READINGS)
    print(str(axes1))
    print()
    return (axes0, axes1)


def average_readings(n):
    x = []
    y = []
    z = []
    for i in range(n):
        axes = a.getAxes()
        x.append(axes['x'])
        y.append(axes['y'])
        z.append(axes['z'])
        sleep(0.01)
    return {'x': mean(x), 'y': mean(y), 'z': mean(z)}


def mean(m):
    return sum(m) / len(m)
