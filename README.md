# AeroGlove — PyDrone (ESP32 gesture-controlled drone)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/thisux1/AeroGlove?style=social)](https://github.com/thisux1/AeroGlove)

Lightweight MicroPython project for an ESP32-based gesture-controlled drone (PyDrone). The device reads an IMU (MPU6500/MPU9250 + AK8963) and maps user gestures to flight commands (throttle, pitch, roll, yaw). This repo contains drivers, BLE utilities and example firmware for the AeroGlove flight controller.

## Key features
- IMU drivers: `mpu6500.py`, `mpu9250.py`, `ak8963.py`
- BLE utilities and example central/peripheral code (`ble_*`, `lib/aioble`)
- Example entry scripts: `boot.py`, `main.py`
- Calibration storage: `accel_cal.json` (keeps calibration data separate from code)

## Repository layout
- `boot.py`, `main.py` — device startup and main loop
- `mpu6500.py`, `mpu9250.py`, `ak8963.py` — sensor drivers
- `ble_advertising.py`, `ble_simple_peripheral.py` — BLE examples
- `lib/aioble/` — bundled aioble BLE library used by examples
- `accel_cal.json` — accelerometer calibration data (keep private if needed)

## Quickstart — publish this repo to GitHub
1. Create/confirm a GitHub repository (e.g. `thisux1/AeroGlove`). You can do this on the GitHub web UI or with the GitHub CLI.

2. From the project root, initialize and push (PowerShell):

```powershell
# if you haven't already
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/AeroGlove.git
git push -u origin main
```

If you prefer to create-and-push in one step with the GitHub CLI:

```powershell
gh auth login
gh repo create thisux1/AeroGlove --public --source=. --remote=origin --push
```

Notes
- Ensure `secrets.py` or any other sensitive file is removed or in `.gitignore` before pushing.
- Replace the remote URL or `thisux1` with your GitHub username if different.

## Flashing / deploying to the ESP32 (Windows PowerShell examples)
Recommended: use `mpremote` (part of the mpremote toolchain). This copies the repository files to the device filesystem.

```powershell
# list connected devices (Windows)
mpremote list

# connect and copy project files to device (adjust the port/URI as needed)
mpremote connect serial://COM3 fs put . /

# or, if mpremote shows a device name like 'usb', use that
mpremote connect usb0 fs put . /
```

Alternative: use `ampy` (older) or `rshell`.

Tips
- Only copy files you need (for faster flashing) e.g. `mpremote fs put main.py /` and `mpremote fs put lib/ /lib`.
- Reboot the device after copying: `mpremote connect serial://COM3 run 'import machine; machine.reset()'`.

## Calibration
- `accel_cal.json` contains accelerometer calibration used at runtime. Keep this file if you need reproducible sensor calibration, or remove it before publishing if it contains sensitive test data.

## Usage
- Power the AeroGlove hardware and ensure the IMU is properly connected (SDA/SCL to ESP32 I2C pins or SPI wiring depending on your driver configuration).
- The `main.py` file contains the gesture-to-command mapping used during flight. Edit and tune thresholds in the sensor/driver files or a dedicated `config.py` as needed.

Since gesture mapping and flight control loops are highly hardware-specific, read the relevant sections in `mpu9250.py`/`mpu6500.py` and `main.py` before flying.

## Hardware (typical)
- ESP32 development board (e.g. ESP32 DevKit)
- IMU: MPU6500 / MPU9250 (+ AK8963 magnetometer)
- Motor ESCs, brushless motors, propellers
- Battery and power distribution
- (Optional) BLE remote device for telemetry/control

## Contributing
- Contributions are welcome. Open an issue first to discuss larger changes.
- Fork the repo, create a feature branch, add tests or examples, and open a pull request.

## License
This project is intended to be open source. Add a `LICENSE` file (MIT recommended) to publish under that license. If you'd like, I can add an `MIT` LICENSE file now.

## CI / Quality
- You can add a GitHub Actions workflow to run linters or static checks on PRs. If you want, I can add a minimal workflow that checks Python formatting or runs basic unit tests.

## Security
- Do not commit device credentials, private keys, or Wi-Fi passwords. Use `secrets.py` locally and add it to `.gitignore`.

## Contacts / Acknowledgements
- Created for the PyDrone community. If you publish, include a short description and a link back to this repository.

---
If you want, I can also:
- add an `MIT` `LICENSE` file,
- create a minimal GitHub Actions workflow,
- prepare a `flash.sh` / `flash.ps1` helper script to simplify device uploads.

Tell me which of those you'd like me to add and I'll make the edits.