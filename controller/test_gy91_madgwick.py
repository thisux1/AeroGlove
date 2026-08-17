from machine import Pin, I2C
import time
from imu_madgwick import MadgwickAHRS
from gy91 import GY91


def main():
    i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
    sensor = GY91(i2c)
    fuser = MadgwickAHRS(beta=0.08)

    last = time.ticks_us()
    while True:
        ax, ay, az, gx, gy, gz = sensor.read_imu()
        now = time.ticks_us()
        dt = (time.ticks_diff(now, last)) / 1_000_000.0
        last = now
        # guard for long pauses
        if dt <= 0 or dt > 0.1:
            dt = 0.005
        fuser.update_imu(gx, gy, gz, ax, ay, az, dt)
        roll, pitch, yaw = fuser.euler()
        temp_c, press_pa = sensor.read_baro()
        print("deg:", tuple(int(v * 57.2958) for v in (roll, pitch, yaw)), "T=", temp_c, "P=", int(press_pa))
        time.sleep_ms(10)


if __name__ == "__main__":
    main()


