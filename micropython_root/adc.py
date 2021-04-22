'''
ADS1115 driver for ESP32 running Micropython

Not fully implemented.
'''

from time import sleep


class ADS1115():
    def __init__(self, i2c, address=72):
        self.i2c = i2c
        self.address = address
        self.config = b'\x85\x83'
        self.fs = 6.144
        self.mode = 0b1
        self.data_rate = 0b100
        self.comp_mode = 0b0
        self.comp_pol = 0b0
        self.comp_lat = 0b0
        self.comp_que = 0b11
        self.channel = "A0"

    def build_config(self, single_shot=True):
        os = 0b1
        mux = None
        pga = None
        mode = self.mode
        data_rate = self.data_rate
        comp_mode = self.comp_mode
        comp_pol = self.comp_pol
        comp_lat = self.comp_lat
        comp_que = self.comp_que

        if self.fs == 6.144:
            pga = 0b000
        elif self.fs == 4.096:
            pga = 0b001
        elif self.fs == 2.048:
            pga = 0b010
        elif self.fs == 1.024:
            pga = 0b011
        elif self.fs == 0.512:
            pga = 0b100
        elif self.fs == 0.256:
            pga = 0b101

        if self.channel is "A0":
            mux = 0b100
        elif self.channel is "A1":
            mux = 0b101
        elif self.channel is "A2":
            mux = 0b110
        elif self.channel is "A3":
            mux = 0b111
        # the following multiplexer configs are differential
        elif self.channel is "A01":
            mux = 0b000
        elif self.channel is "A03":
            mux = 0b001
        elif self.channel is "A13":
            mux = 0b010
        elif self.channel is "A23":
            mux = 0b011
        else:
            raise TypeError(str(self.channel) + "was not a valid input configuration.")

        # writing the 15th (msb) as 1 will tell it to do a reading
        if single_shot is True:
            os = 0b1
        else:
            os = 0b0
        # config is the 16-bit configuration register of the ADS1115.
        # Here we concatenate the above configuration variables
        config = ((os << 15) | (mux << 12) | (pga << 9) | (mode << 8) | (data_rate << 5) | (
            comp_mode << 4) | (comp_pol << 3) | (comp_lat << 2) | (comp_que))
        config = config.to_bytes(2, 'big')  # convert int to bytes literal
        self.config = config

    def get_voltage(self, channel="A01", refresh_config=True):
        self.channel = channel
        if refresh_config:
            self.build_config()
        config = self.config
        # writing the 15th (msb) as 1 will tell it to do a reading
        # write to config register (register 1)
        self.i2c.writeto_mem(self.address, 1, config)
        while not (int.from_bytes(
                self.i2c.readfrom_mem(self.address, 1, 2), "big") & (0b1 << 15)):
            # reading msb of 0 from the config register means a conversion is happening
            # wait until conversion is done
            sleep(0.01)
        # reading 0b1 from the conversion register is equal to FS / 2^15
        return int.from_bytes(
            self.i2c.readfrom_mem(self.address, 0, 2), "big") / 32768 * self.fs
