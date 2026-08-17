import bluetooth
import time
from machine import Pin, I2C
from imu_madgwick import MadgwickAHRS
from gy91 import GY91


NUS_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
NUS_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")


def make_dabble_packet(x_norm: int, y_norm: int, buttons_mask: int = 0):
    # Formato esperado pelo parse_dabble_packet do seu drone
    # 0xFF 0x01 0x02 0x01 0x02 <buttons> <x> <y>
    x_b = max(0, min(255, x_norm + 128))
    y_b = max(0, min(255, y_norm + 128))
    return bytes((0xFF, 0x01, 0x02, 0x01, 0x02, buttons_mask & 0xFF, x_b, y_b))


def map_axis(rad: float, full_scale_deg: float = 30.0) -> int:
    # rad -> [-100, 100] saturado em ~±full_scale_deg
    fs = full_scale_deg * 0.01745329252
    v = rad / fs
    v = -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)
    return int(v * 100)


class NUSClient:
    def __init__(self, target_name: str = "PYDRONE_DBG"):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.target_name = target_name
        self.conn_handle = None
        self.rx_handle = None

    def _scan_and_connect(self, timeout_ms: int = 8000):
        found = None
        done = False

        def _irq(event, data):
            nonlocal found, done
            if event == 5:  # _IRQ_SCAN_RESULT
                addr_type, addr, adv_type, rssi, adv_data = data
                try:
                    name = bluetooth.decode_name(adv_data)
                except Exception:
                    name = None
                if name == self.target_name:
                    found = (addr_type, bytes(addr))
            elif event == 6:  # _IRQ_SCAN_DONE
                done = True

        self.ble.irq(_irq)
        self.ble.gap_scan(timeout_ms, 30000, 30000)
        t0 = time.ticks_ms()
        while not done and time.ticks_diff(time.ticks_ms(), t0) < timeout_ms + 1000:
            time.sleep_ms(50)
        if not found:
            raise OSError("NUS target not found")

        addr_type, addr = found
        # Connect
        ev = {}
        def _irq2(event, data):
            if event == 7:  # _IRQ_PERIPHERAL_CONNECT
                conn_handle, *_ = data
                ev['conn'] = conn_handle
            elif event == 9:  # _IRQ_GATTC_SERVICE_RESULT
                conn_handle, start_handle, end_handle, uuid = data
                if uuid == NUS_UUID:
                    ev['svc'] = (start_handle, end_handle)
            elif event == 11:  # _IRQ_GATTC_CHARACTERISTIC_RESULT
                conn_handle, def_handle, value_handle, properties, uuid = data
                if uuid == NUS_RX_UUID:
                    ev['rx'] = value_handle
            elif event == 8:  # _IRQ_PERIPHERAL_DISCONNECT
                ev['disc'] = True

        self.ble.irq(_irq2)
        self.ble.gap_connect(addr_type, addr)
        t0 = time.ticks_ms()
        while 'conn' not in ev and time.ticks_diff(time.ticks_ms(), t0) < 5000:
            time.sleep_ms(50)
        if 'conn' not in ev:
            raise OSError('connect timeout')
        self.conn_handle = ev['conn']

        # discover services/chars
        self.ble.gattc_discover_services(self.conn_handle)
        time.sleep_ms(200)
        if 'svc' not in ev:
            raise OSError('NUS service not found')
        sh, eh = ev['svc']
        self.ble.gattc_discover_characteristics(self.conn_handle, sh, eh)
        time.sleep_ms(200)
        if 'rx' not in ev:
            raise OSError('NUS RX char not found')
        self.rx_handle = ev['rx']

    def write(self, data: bytes):
        if self.conn_handle is None or self.rx_handle is None:
            self._scan_and_connect()
        self.ble.gattc_write(self.conn_handle, self.rx_handle, data, 1)


def main(target_name: str = "PYDRONE_DBG", btn_up_pin: int = 1, btn_down_pin: int = 2, btn_arm_pin: int = 3):
    i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
    sensor = GY91(i2c)
    fuser = MadgwickAHRS(beta=0.08)
    client = NUSClient(target_name=target_name)
    # botões com pull-up
    btn_up = Pin(btn_up_pin, Pin.IN, Pin.PULL_UP)
    btn_dn = Pin(btn_down_pin, Pin.IN, Pin.PULL_UP)
    btn_arm = Pin(btn_arm_pin, Pin.IN, Pin.PULL_UP)

    last = time.ticks_us()
    arm_sent = 0
    while True:
        ax, ay, az, gx, gy, gz = sensor.read_imu()
        now = time.ticks_us()
        dt = (time.ticks_diff(now, last)) / 1_000_000.0
        last = now
        if dt <= 0 or dt > 0.1:
            dt = 0.01
        fuser.update_imu(gx, gy, gz, ax, ay, az, dt)
        roll, pitch, yaw = fuser.euler()

        x_norm = map_axis(roll)   # roll -> eixo X
        y_norm = map_axis(pitch)  # pitch -> eixo Y
        # buttons: triangle=0x04 (arm), circle=0x08 (thr+), cross=0x10 (disarm), square=0x20 (thr-)
        buttons = 0
        if not btn_up.value():
            buttons |= 0x08
        if not btn_dn.value():
            buttons |= 0x20
        if not btn_arm.value():
            # emite breve pulso de arm (triangle). Se segurar >1s, manda disarm (cross)
            if arm_sent == 0:
                buttons |= 0x04
                arm_sent = now
            elif time.ticks_diff(now, arm_sent) > 1_000_000:
                buttons |= 0x10
        else:
            arm_sent = 0

        pkt = make_dabble_packet(x_norm, y_norm, buttons_mask=buttons)
        try:
            client.write(pkt)
        except OSError:
            # tenta reconectar na próxima iteração
            client.conn_handle = None
            client.rx_handle = None
        time.sleep_ms(20)


if __name__ == "__main__":
    main()


