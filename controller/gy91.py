"""
GY-91 convenience wrapper: MPU925x + BMP280 on same I2C bus.
"""

from machine import I2C
from .mpu925x import MPU925x
from .bmp280_min import BMP280


class GY91:
    def __init__(self, i2c: I2C, ad0_high: bool = False, bmp_addr: int = 0x76):
        self.mpu = MPU925x(i2c=i2c, ad0_high=ad0_high)
        self.bmp = BMP280(i2c=i2c, addr=bmp_addr)

    def read_imu(self):
        return self.mpu.read()  # ax, ay, az (g), gx, gy, gz (rad/s)

    def read_baro(self):
        return self.bmp.read()  # temp C, pressure Pa


