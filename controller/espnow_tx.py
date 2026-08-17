import network
import espnow
from machine import Pin, I2C
import time
from imu_madgwick import MadgwickAHRS
from gy91 import GY91


def map_cmd(x: float, deadband: float = 0.02, expo: float = 0.3) -> float:
    # x in [-1,1] -> with deadband/expo -> [1000,2000]
    if abs(x) < deadband:
        x = 0.0
    # simple expo
    x = (1 - expo) * x + expo * (x * abs(x))
    return 1500 + 500 * x


def main(peer_mac: bytes):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    e = espnow.ESPNow()
    e.active(True)
    e.add_peer(peer_mac)

    i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
    sensor = GY91(i2c)
    fuser = MadgwickAHRS(beta=0.08)

    last = time.ticks_us()
    seq = 0
    while True:
        ax, ay, az, gx, gy, gz = sensor.read_imu()
        now = time.ticks_us()
        dt = (time.ticks_diff(now, last)) / 1_000_000.0
        last = now
        if dt <= 0 or dt > 0.1:
            dt = 0.01
        fuser.update_imu(gx, gy, gz, ax, ay, az, dt)
        roll, pitch, yaw = fuser.euler()

        # normalize to [-1,1] for small angles (~30deg full scale)
        scale = 1.0 / 0.523599  # ~30deg in rad
        ch_roll = map_cmd(max(-1.0, min(1.0, roll * scale)))
        ch_pitch = map_cmd(max(-1.0, min(1.0, -pitch * scale)))
        ch_yaw = map_cmd(max(-1.0, min(1.0, yaw * scale)))
        ch_thr = 1500  # placeholder, substitua por potenciômetro/botão

        payload = bytearray(14)
        payload[0] = (seq >> 8) & 0xFF
        payload[1] = seq & 0xFF
        def w16(i, v):
            payload[i] = (int(v) >> 8) & 0xFF
            payload[i + 1] = int(v) & 0xFF
        w16(2, ch_thr)
        w16(4, ch_roll)
        w16(6, ch_pitch)
        w16(8, ch_yaw)
        temp_c, _ = sensor.read_baro()
        w16(10, int((temp_c + 40) * 10))
        payload[12] = 0
        payload[13] = 0

        e.send(peer_mac, payload)
        seq = (seq + 1) & 0xFFFF
        time.sleep_ms(10)


if __name__ == "__main__":
    # substitua pelo MAC do drone (WLAN STA)
    main(b"\xff\xff\xff\xff\xff\xff")


