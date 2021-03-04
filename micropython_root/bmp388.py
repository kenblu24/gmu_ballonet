from machine import Pin, I2C
from time import sleep


i2c = I2C(scl=Pin(22), sda=Pin(21))  # must specify pins for some reason

ADDRESS = 118  # 0h76 = 118. Default I2C address of BMP388

# Register addresses
PWR_CTRL = 0x1b
DATA_0 = 0x04  # least significant byte of pressure data
DATA_3 = 0x07  # least significant byte of temperature data
CHIP_ID = 0x00


def get_chip_id():
    return int.from_bytes(i2c.readfrom_mem(ADDRESS, CHIP_ID, 1), "big")


def single_read(which="Both"):
    temperature = None
    pressure = None
    which = which.lower()
    if which is "both":
        temp_en = 1
        press_en = 1
    elif which is "temperature":
        temp_en = 1
        press_en = 0
    elif which is "pressure":
        temp_en = 0
        press_en = 1
    else:
        raise TypeError(" was not a valid property to read.")
    config = ((0b11 << 4) | (temp_en << 1) | (press_en))
    config = config.to_bytes(1, "big")  # convert int to bytes literal
    i2c.writeto_mem(ADDRESS, 1, config)  # setting power mode to 0b11 will tell it to do a reading

    if which is "both":
        burst_read = i2c.readfrom_mem(ADDRESS, DATA_0, 6)
        pressure = burst_read[0:3]
        temperature = burst_read[3:7]
    elif which is "temperature":
        temperature = i2c.readfrom_mem(ADDRESS, DATA_3, 3)
    elif which is "pressure":
        pressure = i2c.readfrom_mem(ADDRESS, DATA_0, 3)

    if temperature:

    return {"Temperature": temperature, "Pressure": pressure}


def get_voltage(channel="A01"):
    config = b'\x85\x83'
    mux = 0b000
    pga = 0b001  # this sets FS on the ADS1115
    mode = 0b1
    data_rate = 0b100
    comp_mode = 0b0
    comp_pol = 0b0
    comp_lat = 0b0
    comp_que = 0b11
    if channel is "A0":
        mux = 0b100
    elif channel is "A1":
        mux = 0b101
    elif channel is "A2":
        mux = 0b110
    elif channel is "A3":
        mux = 0b111
    # the following multiplexer configs are differential
    elif channel is "A01":
        mux = 0b000
    elif channel is "A03":
        mux = 0b001
    elif channel is "A13":
        mux = 0b010
    elif channel is "A23":
        channel = 0b011
    else:
        raise TypeError(channel + " was not a valid input configuration.")
    # config is the 16-bit configuration register of the ADS1115.
    # Here we concatenate the above configuration variables
    config = ((0b1 << 15) | (mux << 12) | (pga << 9) | (mode << 8) | (data_rate << 5) | (
        comp_mode << 4) | (comp_pol << 3) | (comp_lat << 2) | (comp_que))
    config = config.to_bytes(2, "big")  # convert int to bytes literal
    i2c.writeto_mem(ADC, 1, config)  # writing the 15th (msb) as 1 will tell it to do a reading
    while not (int.from_bytes(i2c.readfrom_mem(ADC, 1, 2), "big") & (0b1 << 15)):
        # reading msb of 0 from the config register means a conversion is happening
        # wait until conversion is done
        sleep(0.01)
    # reading 0b1 from the conversion register is equal to FS / 2^15
    FS = 4.096
    return int.from_bytes(i2c.readfrom_mem(ADC, 0, 2), "big") / 32768 * FS


def get_temperature():
    R1 = 99.2 * 1000
    Vref1 = get_voltage("A3")
    Vo = get_voltage("A0")
    Rntc = R1 / (Vref1 / Vo - 1)
    return epcos.get_temperature(Rntc)


def get_temperature_fahrenheit():
    return get_temperature() * 9 / 5 + 32
