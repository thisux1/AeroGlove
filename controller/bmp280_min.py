"""
Very small BMP280 reader (temperature/pressure) for MicroPython.
Default I2C address is 0x76 (or 0x77 if SDO high).
"""

from machine import I2C
import struct
import time


class BMP280:
    def __init__(self, i2c: I2C, addr: int = 0x76):
        self.i2c = i2c
        self.addr = addr
        # Read calibration
        self._cal = self.i2c.readfrom_mem(self.addr, 0x88, 24)
        (self.dig_T1, self.dig_T2, self.dig_T3,
         self.dig_P1, self.dig_P2, self.dig_P3, self.dig_P4,
         self.dig_P5, self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9) = struct.unpack('<HhhHhhhhhhhh', self._cal)
        # ctrl_meas: temp/press oversampling x1, normal mode
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')
        # config: standby 0.5ms, filter off
        self.i2c.writeto_mem(self.addr, 0xF5, b'\x00')
        time.sleep_ms(10)

    def _read_raw(self):
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 6)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return adc_t, adc_p

    def read(self):
        adc_t, adc_p = self._read_raw()

        # Temperature compensation
        var1 = (((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temp_c = (t_fine * 5 + 128) >> 8
        temp_c = temp_c / 100.0

        # Pressure compensation
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return temp_c, 0.0
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        pressure_pa = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        pressure_pa = pressure_pa / 256.0
        return temp_c, pressure_pa


