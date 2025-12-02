# backup_esp32

MicroPython project for ESP32 (contains code for MPU6500/MPU9250, AK8963 magnetometer, BLE utilities and example scripts).

What this repo contains
- `main.py`, `boot.py` - entry points for the device
- `mpu6500.py`, `mpu9250.py`, `ak8963.py` - sensor drivers
- `ble_*` and `lib/aioble` - BLE peripheral/central code
- `accel_cal.json` - accelerometer calibration data (check for secrets before committing)

How to publish this to GitHub
1. Initialize a local git repo (run in the project root):

   git init
   git add .
   git commit -m "Initial commit"

2. Create a repository on GitHub (via the website or `gh repo create`) and push:

   git branch -M main
   git remote add origin <your-git-remote-URL>
   git push -u origin main

Using the GitHub CLI (optional):

   gh repo create <repo-name> --public --source=. --remote=origin --push

Notes
- Make sure `secrets.py` or any sensitive files are excluded or removed before pushing.
- To upload files to the ESP32 from this repo, use `mpremote` or `ampy` after cloning/pulling to your dev machine.

Example: using mpremote to push files to device

   mpremote connect serial://COM3 fs put . /

(Adjust the serial port and commands for your environment.)

License
- Add a `LICENSE` file if you want to publish under an open-source license (MIT suggested).