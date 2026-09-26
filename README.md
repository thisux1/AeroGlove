<div align="center">
  <a href="#root"><img src="./docs/banner.svg?v=2" alt="AeroGlove" width="100%"/></a>
</div>

> 🇧🇷 [Versão em Português](docs/README.pt-BR.md)

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <pre lang="bash"><code>$ aeroglove / briefing
----------------------------------------------
• airframe : pyDrone quad-X microdrone
• input    : hand attitude, glove-mounted IMU
• sensor   : GY-91 · MPU-9250 9-DOF + BMP280
• channels : THR / ROLL / PITCH / YAW (µs)
• shaping  : deadband 0.02 · expo 0.3 · ±30° FS
• packet   : 14 B binary @ 100 Hz, ESP-NOW</code></pre>
    </td>
    <td width="50%" valign="top">
      <pre lang="python"><code>class Glove:
    fusion   = MadgwickAHRS(beta=0.08)  # 100 Hz
    link     = "esp-now | ble-nus fallback"
    failsafe = "cut motors > 200 ms silent"
    mcu      = "esp32-s3 · micropython"
    tooling  = ["esptool", "mpremote"]</code></pre>
    </td>
  </tr>
</table>

### ❯ badges

<p align="left">
  <img src="https://img.shields.io/badge/MicroPython-v1.20+-black?style=flat-square&logo=python&logoColor=38BDF8&labelColor=030712" alt="MicroPython" />
  <img src="https://img.shields.io/badge/ESP--NOW-2.4GHz-black?style=flat-square&logo=espressif&logoColor=E7352C&labelColor=030712" alt="ESP-NOW" />
  <img src="https://img.shields.io/badge/ESP32--S3-Dual_Core-black?style=flat-square&logo=espressif&logoColor=white&labelColor=030712" alt="ESP32-S3" />
  <img src="https://img.shields.io/badge/IMU-GY--91_/_MPU9250-black?style=flat-square&logo=sensor&logoColor=38BDF8&labelColor=030712" alt="IMU GY-91" />
  <img src="https://img.shields.io/badge/AHRS-Madgwick_100Hz-black?style=flat-square&logo=speedtest&logoColor=00F0FF&labelColor=030712" alt="Madgwick AHRS" />
  <img src="https://img.shields.io/badge/BLE-Nordic_NUS-black?style=flat-square&logo=bluetooth&logoColor=0082FC&labelColor=030712" alt="BLE NUS" />
  <img src="https://img.shields.io/badge/License-MIT-black?style=flat-square&logo=opensourceinitiative&logoColor=green&labelColor=030712" alt="License MIT" />
</p>

---

### ❯ what_is_this

AeroGlove is a wearable glove controller that flies a quadcopter with bare hand
gestures. An ESP32-S3 running MicroPython samples a GY-91 IMU (MPU-9250 9-DOF
plus BMP280 barometer) over I2C at 400 kHz, fuses orientation with Madgwick
AHRS at 100 Hz (β = 0.08), maps hand attitude to the four RC channels
(throttle, roll, pitch, yaw) with deadband and exponential shaping, and streams
14-byte binary packets over ESP-NOW to a receiver on the drone. BLE NUS is
wired in as a fallback link. If the receiver hears nothing for more than
200 ms, it cuts the motors.

The target airframe is the [pyDrone](https://github.com/01studio-lab/pyDrone)
quad-X platform from 01Studio.

---

### ❯ signal_chain

<div align="center">
  <img src="./docs/architecture.svg?v=2" alt="AeroGlove signal chain" width="100%"/>
</div>

From knuckle to propeller, one loop iteration:

1. **Sample:** raw acceleration, angular rate and barometric pressure read off
   the GY-91 over I2C at 400 kHz.
2. **Fuse:** `MadgwickAHRS` integrates quaternions at 100 Hz with β = 0.08,
   cancelling gyro drift and producing roll, pitch and yaw angles.
3. **Map:** forward/back tilt drives pitch, lateral tilt drives roll, wrist
   rotation drives yaw. A 0.02 deadband kills jitter around neutral and an
   expo curve (0.3) softens the center stick feel; full scale is about ±30°.
4. **Transmit:** channels are packed into a fixed 14-byte frame (sequence,
   four u16 channel values, temperature, reserved) and sent over ESP-NOW every
   10 ms. Sub-10 ms air latency; BLE NUS client available as fallback.
5. **Fail safe:** the onboard receiver feeds the quad mixer and runs a
   watchdog: more than 200 ms without a packet and the motors shut down.

---

### ❯ hardware

| Component | Recommended spec | Role |
| :--- | :--- | :--- |
| MCU | ESP32-S3 dual-core (or standard ESP32) | Glove and drone compute |
| IMU | GY-91 module (MPU-9250 + BMP280) | Gyro, accel, magnetometer, barometer |
| Glove power | 3.7 V LiPo (500-1200 mAh) | Untethered supply |
| Charger | TP4056 module with protection | USB-C / micro-USB charging |
| Wearable frame | Sports/textile glove + 3D-printed case | Mounts electronics on the hand |
| Airframe | Quad-X microdrone | Flight platform ([pyDrone 01Studio](https://github.com/01studio-lab/pyDrone)) |

---

### ❯ pinout

Wire the GY-91 to the ESP32's I2C bus:

```
  GY-91 module                ESP32 / ESP32-S3
 ┌──────────────┐            ┌──────────────────┐
 │     VCC      │───────────▶│  3.3V            │
 │     GND      │───────────▶│  GND             │
 │     SDA      │───────────▶│  GPIO 8  (I2C)   │
 │     SCL      │───────────▶│  GPIO 9  (I2C)   │
 └──────────────┘            └──────────────────┘
```

> Check your board's pinout and confirm the bus is 3.3 V before powering up.

---

### ❯ flash_and_fly

**1. Burn MicroPython onto the ESP32**

```bash
pip install esptool

# wipe flash
esptool.py --chip esp32s3 --port COM3 erase_flash

# write the MicroPython binary
esptool.py --chip esp32s3 --port COM3 write_flash -z 0x0 <firmware.bin>
```

Use your serial port (`COM3` on Windows, `/dev/ttyUSB0` on Linux).

**2. Push the firmware with mpremote**

```bash
pip install mpremote
mpremote list

# transmitter files (glove)
mpremote connect COM3 fs cp controller/espnow_tx.py :main.py
mpremote connect COM3 fs cp controller/imu_madgwick.py :imu_madgwick.py
mpremote connect COM3 fs cp controller/gy91.py :gy91.py
mpremote connect COM3 fs cp controller/mpu925x.py :mpu925x.py
mpremote connect COM3 fs cp controller/bmp280_min.py :bmp280_min.py
mpremote connect COM3 fs cp controller/ble_nus_client.py :ble_nus_client.py

mpremote connect COM3 run "import machine; machine.reset()"
```

**3. Calibrate the IMU neutral pose**

1. Rest the glove on a flat surface, hand open in a neutral pose.
2. Power the board (or run the calibration script).
3. Keep the hand still for 10-15 s so the Madgwick filter converges on the
   gravity vector (1.0 g on Z).

**4. Sanity-check over REPL**

```bash
mpremote connect COM3 repl
```

```python
from machine import Pin, I2C
from gy91 import GY91

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
sensor = GY91(i2c)

print("IMU:", sensor.read_imu())   # ax, ay, az, gx, gy, gz
print("Baro:", sensor.read_baro()) # °C, Pa
```

---

### ❯ bench_test

> **Safety first: run every early test with the propellers off**, or on a
> protected bench rig.

1. Hardware check: motor screws, power wiring, LiPo charge level.
2. Pairing: power the glove and the drone; the status LED reports the
   ESP-NOW/BLE link sync.
3. Bench test (no props):
   - Tilt hand forward → rear motors spin up (pitch down / forward).
   - Tilt hand right → left-side motors compensate (roll right).
   - Rotate wrist clockwise → diagonal motor pairs respond (yaw CW).
4. Flight test: with props on, start in an open flat area with short low
   hops to validate command stability.

---

### ❯ repo_map

<pre lang="text"><code>controller/                  glove transmitter firmware (AeroGlove)
  ├── espnow_tx.py           main loop, ESP-NOW sender @ 100 Hz
  ├── imu_madgwick.py        Madgwick AHRS orientation filter
  ├── gy91.py                composite driver, GY-91 (9-DOF + baro)
  ├── mpu925x.py             minimal MPU-9250 / MPU-9255 driver
  ├── bmp280_min.py          BMP280 barometric altitude driver
  ├── ble_nus_client.py      BLE Nordic UART fallback client
  └── test_gy91_madgwick.py  sensor convergence and calibration tests
drone/                       receiver firmware on the aircraft
  └── espnow_rx.py           ESP-NOW RX, 4CH decode, 200 ms failsafe
docs/                        banner.svg · architecture.svg · README.pt-BR.md
LICENSE                      MIT</code></pre>

---

### ❯ references

- Base airframe: [pyDrone (01studio-lab)](https://github.com/01studio-lab/pyDrone)
- Sensor fusion: Madgwick, S. O. (2010), *An efficient orientation filter for
  inertial and inertial/magnetic sensor arrays*

---

Built by **Thiago Araújo** ([@thisux1](https://github.com/thisux1)).
Released under the [MIT License](LICENSE).
