from machine import Pin, PWM


class drv8833:
    def __init__(self, pwm_frequency, sleep_pin, fault_pin, in1_pin, in2_pin, in3_pin, in4_pin):
        self.sleep = Pin(sleep_pin, Pin.OUT, value=0)
        self.fault = Pin(fault_pin, Pin.IN, Pin.PULL_UP)

        self.pin_in1 = in1_pin
        self.pin_in2 = in2_pin
        self.pwm_frequency = pwm_frequency
        self.in1 = PWM(Pin(self.pin_in1), freq=pwm_frequency, duty=0)
        self.in2 = Pin(self.pin_in2, Pin.OUT)
        self.in2.off()
        self.sleep.off()

    def emergency_stop(self):
        ioall = (self.in1, self.in2)
        for io in ioall:
            if type(io) is PWM:
                io.deinit()
            if type(io) is Pin:
                io.off()

    def power(self, duty=None, direction=None):
        if duty is None:
            return self.in1.duty()
        if duty is 0:
            self.sleep.off()
        else:
            self.sleep.on()
        new_duty = min(1023, max(0, int(duty * 1024)))
        if direction is None:
            if type(self.in1) is PWM:
                self.in1.duty(new_duty)
                self.in2.off()
            elif type(self.in2) is PWM:
                self.in2.duty(new_duty)
                self.in1.off()
            pass
        elif direction in ("Forward", "Forward Coast", "Reverse Brake"):
            if type(self.in1) is PWM and type(self.in2) is Pin:
                self.in1.duty(new_duty)
            else:
                if type(self.in2) is PWM:
                    self.in2.deinit()
                self.in1 = PWM(Pin(self.pin_in1), freq=self.pwm_frequency, duty=new_duty)
                self.in2 = Pin(self.pin_in2, Pin.OUT)
            if "Forward" in direction:
                self.in2.off()
            elif "Reverse" in direction:
                self.in2.on()
        elif direction in ("Reverse", "Reverse Coast", "Forward Brake"):
            if type(self.in1) is Pin and type(self.in2) is PWM:
                self.in2.duty(new_duty)
            else:
                if type(self.in1) is PWM:
                    self.in1.deinit()
                self.in1 = Pin(self.pin_in1, Pin.OUT)
                self.in2 = PWM(Pin(self.pin_in2), freq=self.pwm_frequency, duty=new_duty)
            if "Forward" in direction:
                self.in1.on()
            elif "Reverse" in direction:
                self.in1.off()
        else:
            raise Exception(str(direction) + " was not a valid direction.")


if __name__ == '__main__':
    # drv8833(pwm_frequency, sleep_pin, fault_pin, in1_pin, in2_pin, in3_pin, in4_pin)
    hbridge = drv8833(1000, 32, 33, 25, 26, None, None)
