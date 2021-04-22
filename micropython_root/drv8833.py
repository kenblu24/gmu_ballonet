from machine import Pin, PWM


# this class controls an individual channel (A or B) on the drv8833
# It is meant to be used as an internal class for the full driver
class MOTOR_BANK:
    def __init__(self, pwm_frequency, in1_pin, in2_pin, duty_callback=None):
        self._pwm_frequency = pwm_frequency
        # Warning! Index change. in1 is [0], in2 is [1]
        self.pins = (in1_pin, in2_pin)
        for pin in self.pins:
            # init both output pins as GPIO
            pin.init(Pin.OUT, value=0)
        # PWM object takes precedence over GPIO output of that pin
        self.out = [self.pins[0], PWM(self.pins[1], freq=pwm_frequency, duty=0)]
        self._direction = "Forward"
        self._duty = 0
        self._duty_int = 0
        self.duty_callback = duty_callback  # called when duty is changed
        # used for setting sleep when all motors off.

    @property
    def duty(self):
        return self._duty

    @duty.setter
    def duty(self, duty):
        # changes internal duty cycle and updates PWM output
        self._duty = duty
        self._duty_int = min(1023, max(0, int(duty * 1024)))
        # change duty cycle while preserving direction
        if type(self.out[0]) is PWM:
            self.out[0].duty(self._duty_int)
        elif type(self.out[1]) is PWM:
            self.out[1].duty(self._duty_int)

        try:
            self.duty_callback()
        except TypeError as e:
            if e == "'NoneType object isn't callable":
                pass
            else:
                raise e

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        # logic to set pin config based on direction
        # See DRV8833 datasheet for more info
        if direction in ("Forward", "Forward Coast", "Reverse Brake"):
            if type(self.out[1]) is PWM:
                self.out[1].deinit()
            self.out[0] = PWM(self.pins[0], freq=self._pwm_frequency, duty=self._duty_int)
            self.out[1] = self.pins[1]
            if "Forward" in direction:
                self.out[1].off()
            elif "Reverse" in direction:
                self.out[1].on()
        elif direction in ("Reverse", "Reverse Coast", "Forward Brake"):
            if type(self.out[0]) is PWM:
                self.out[0].deinit()
            self.out[0] = self.pins[0]
            self.out[1] = PWM(self.pins[1], freq=self._pwm_frequency, duty=self._duty_int)
            if "Forward" in direction:
                self.out[0].on()
            elif "Reverse" in direction:
                self.out[0].off()
        else:
            raise Exception(str(direction) + " was not a valid direction.")

    @property
    def pwm_frequency(self):
        return self._pwm_frequency

    @pwm_frequency.setter
    def pwm_frequency(self, frequency):
        # changes internal pwm_frequency and updates PWM output
        self._pwm_frequency = frequency
        if type(self.out[0]) is PWM:
            self.out[0].freq(self._pwm_frequency)
        elif type(self.out[1]) is PWM:
            self.out[1].freq(self._pwm_frequency)


class DRV8833:
    def __init__(self, pwm_frequency, sleep_pin, fault_pin, in1_pin, in2_pin, in3_pin, in4_pin):
        # this class controls stuff between banks.
        self.sleep = sleep_pin  # Active LOW (DRV8833 enabled when HIGH)
        self.sleep.init(mode=Pin.OUT, value=0)
        self.fault = fault_pin  # NOT IMPLEMENTED but can read with this.fault.value
        self.fault.init(mode=Pin.IN)

        self.sleep.off()

        self.motor = dict()
        if in1_pin and in2_pin:
            self.motor['A'] = MOTOR_BANK(pwm_frequency, in1_pin, in2_pin, self.duty_callback)
        if in3_pin and in4_pin:
            self.motor['B'] = MOTOR_BANK(pwm_frequency, in3_pin, in4_pin, self.duty_callback)

    def emergency_stop(self):
        # Attempts to shut off all pins in all defined motor channels.
        # May require re-init to use motors afterwards.
        for motor in self.motor.values():
            for io in motor.out:
                if type(io) is PWM:
                    io.deinit()
                if type(io) is Pin:
                    io.off()
            for io in motor.pins:
                if type(io) is Pin:
                    io.init(Pin.OUT, value=0)
        print("Emergency Stop called.")

    def duty_callback(self):
        # set SLEEP pin HIGH if all motors off, else LOW
        all_off = True
        for motor in self.motor.values():
            if motor.duty is not 0:
                all_off = False
        self.sleep.value(int(not all_off))


if __name__ == '__main__':
    # drv8833(pwm_frequency, sleep_pin, fault_pin, in1_pin, in2_pin, in3_pin, in4_pin)
    hbridge = DRV8833(1000, Pin(32), Pin(33), Pin(25), Pin(26), Pin(27), Pin(14))
    # examples
    # duty cycle can be set between 0 to 1
    # hbridge.motor['A'].duty = 0.5
    # hbridge.motor['B'].direction = "Forward"
    # hbridge.motor['A'].pwm_frequency = 100
