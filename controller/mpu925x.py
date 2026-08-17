"""
MPU925x (MPU9250/MPU9255) minimal I2C driver for MicroPython.

Notes
- Uses only accel and gyro (magnetometer via AK8963 not implemented here).
- Exposes readings in g and rad/s.
- Device address default 0x68, set ad0_high=True for 0x69.
"""

from machine import I2C
from math import pi
import time


class MPU925x:
    def __init__(self, i2c: I2C, ad0_high: bool = False):
        self.i2c = i2c
        self.addr = 0x69 if ad0_high else 0x68

        # Registers
        self._PWR_MGMT_1 = 0x6B
        self._SMPLRT_DIV = 0x19
        self._CONFIG = 0x1A
        self._GYRO_CONFIG = 0x1B
        self._ACCEL_CONFIG = 0x1C
        self._ACCEL_CONFIG2 = 0x1D
        self._ACCEL_XOUT_H = 0x3B

        # Wake device
        self._write(self._PWR_MGMT_1, 0x01)  # clock PLL X
        time.sleep_ms(50)

        # Default ranges: accel ±2g, gyro ±2000 dps, DLPF on
        self.set_accel_range(2)
        self.set_gyro_range(2000)
        self._write(self._CONFIG, 0x03)  # DLPF ~44/42 Hz
        self._write(self._ACCEL_CONFIG2, 0x03)
        self._write(self._SMPLRT_DIV, 0x00)  # sample rate = gyro rate / (1+div)

    def _read(self, reg: int, n: int) -> bytes:
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def _write(self, reg: int, val: int) -> None:
        self.i2c.writeto_mem(self.addr, reg, bytes([val & 0xFF]))

    def set_accel_range(self, g: int) -> None:
        # 2, 4, 8, 16 g
        scale_bits = {2: 0, 4: 1, 8: 2, 16: 3}[g]
        self._write(self._ACCEL_CONFIG, scale_bits << 3)
        self._accel_lsb_per_g = {2: 16384.0, 4: 8192.0, 8: 4096.0, 16: 2048.0}[g]

    def set_gyro_range(self, dps: int) -> None:
        # 250, 500, 1000, 2000 dps
        scale_bits = {250: 0, 500: 1, 1000: 2, 2000: 3}[dps]
        self._write(self._GYRO_CONFIG, scale_bits << 3)
        self._gyro_lsb_per_dps = {250: 131.0, 500: 65.5, 1000: 32.8, 2000: 16.4}[dps]

    def read_raw(self):
        buf = self._read(self._ACCEL_XOUT_H, 14)
        def _s16(h, l):
            v = (h << 8) | l
            return v - 65536 if v & 0x8000 else v
        ax = _s16(buf[0], buf[1])
        ay = _s16(buf[2], buf[3])
        az = _s16(buf[4], buf[5])
        # temp = _s16(buf[6], buf[7])  # not used
        gx = _s16(buf[8], buf[9])
        gy = _s16(buf[10], buf[11])
        gz = _s16(buf[12], buf[13])
        return ax, ay, az, gx, gy, gz

    def read(self):
        ax, ay, az, gx, gy, gz = self.read_raw()
        # accel in g
        ag = 1.0 / self._accel_lsb_per_g
        ax_g = ax * ag
        ay_g = ay * ag
        az_g = az * ag
        # gyro in rad/s
        gdps = 1.0 / self._gyro_lsb_per_dps
        d2r = pi / 180.0
        gx_rs = gx * gdps * d2r
        gy_rs = gy * gdps * d2r
        gz_rs = gz * gdps * d2r
        return ax_g, ay_g, az_g, gx_rs, gy_rs, gz_rs


