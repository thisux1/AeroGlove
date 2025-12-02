# main.py - BLE Gesture Controller com Switch Take Off/Landing para pyDrone
import ujson
import time
import uasyncio as asyncio
from mpu9250 import MPU9250
from machine import I2C, Pin
import bluetooth
from math import atan2, degrees

# --- Configurações ---
DRONE_NAME = "pyDrone"
EXPECTED_MAC = "AA:BB:CC:11:22:33".upper()  # Ajuste para seu drone
TARGET_MAC_BYTES = b'\xae\x79\x04\xe0\x88\x98'  # Ajuste conforme o MAC do seu drone

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

_IRQ_SCAN_RESULT          = 5
_IRQ_SCAN_DONE            = 6
_IRQ_PERIPHERAL_CONNECT   = 7
_IRQ_PERIPHERAL_DISCONNECT= 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_SERVICE_DONE   = 10
_IRQ_GATTC_CHARACTERISTIC_RESULT = 11
_IRQ_GATTC_CHARACTERISTIC_DONE = 12
_IRQ_GATTC_WRITE_DONE = 17

def _decode_name_from_adv(adv_data):
    if not adv_data: return None
    i = 0
    L = len(adv_data)
    while i + 1 < L:
        length = adv_data[i]
        if length == 0: break
        if i + length >= L: break
        ad_type = adv_data[i + 1]
        if ad_type == 0x09 or ad_type == 0x08:
            start = i + 2
            name_bytes = adv_data[start:start + (length - 1)]
            try: return name_bytes.decode('utf-8', 'ignore')
            except: return str(name_bytes)
        i += 1 + length
    return None

def addr_bytes_to_hex(addr):
    try: return ':'.join('{:02X}'.format(b) for b in addr)
    except: return str(addr)

def addr_bytes_reversed(addr):
    try: return ':'.join('{:02X}'.format(b) for b in reversed(addr))
    except: return str(addr)

class BLEGestureController:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._conn_handle = None
        self._uart_rx_handle = None
        self._scan_callback = None
        self._scanning = False
        self._should_run = True

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            try:
                if len(data) == 3:
                    addr_type, addr, third = data
                    adv_data = third if isinstance(third, (bytes, bytearray)) else b""
                elif len(data) >= 5:
                    addr_type, addr, adv_type, rssi, adv_data = data[:5]
                else:
                    addr_type, addr = data[:2]; adv_data = b""
            except Exception as e:
                print("[BLE] Erro ao desempacotar scan result:", e)
                return

            addr_hex = addr_bytes_to_hex(addr) if addr else "?"
            addr_rev_hex = addr_bytes_reversed(addr) if addr else "?"
            device_name = _decode_name_from_adv(adv_data) if adv_data else None

            is_drone = False
            if device_name == DRONE_NAME:
                print(f"[BLE] Encontrado drone pelo nome: {device_name} ({addr_hex})")
                is_drone = True
            elif EXPECTED_MAC and (addr_hex == EXPECTED_MAC or addr_rev_hex == EXPECTED_MAC):
                print(f"[BLE] Encontrado drone pelo MAC: {addr_hex}/{addr_rev_hex}")
                is_drone = True
            elif addr == TARGET_MAC_BYTES or addr == bytes(reversed(TARGET_MAC_BYTES)):
                print(f"[BLE] Encontrado drone pelo MAC bytes (direto/invertido)")
                is_drone = True

            if is_drone:
                try:
                    self._ble.gap_scan(None)
                except Exception:
                    pass
                if self._scan_callback:
                    self._scan_callback(addr_type, addr)
                return

        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
            print(f"[BLE] Conectado ao drone: {addr_bytes_to_hex(addr)} (handle {conn_handle})")
            try: self._ble.gattc_discover_services(self._conn_handle)
            except Exception as e: print(f"[BLE] Erro ao descobrir serviços: {e}")

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            print(f"[BLE] Drone desconectado. Tentando reconnect...")
            self._conn_handle = None
            self._uart_rx_handle = None
            if self._should_run:
                self.scan_and_connect(scan_time_ms=30000)

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if str(uuid).upper() == str(_UART_UUID).upper():
                print(f"[BLE] Serviço UART encontrado: {uuid}")
                self._ble.gattc_discover_characteristics(conn_handle, start_handle, end_handle)

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if str(uuid).upper() == str(_UART_RX_CHAR).upper():
                self._uart_rx_handle = value_handle
                print(f"[BLE] Characteristic RX encontrada: {value_handle}")

    def scan_and_connect(self, scan_time_ms=30000):
        print(f"[BLE] Scan de {scan_time_ms//1000}s iniciado, procurando drone por nome/MAC.")
        self._scan_callback = self._connect_to_drone
        self._scanning = True
        try: self._ble.gap_scan(scan_time_ms, 30000, 30000)
        except Exception as e: print("[BLE] Erro ao iniciar scan:", e)

    def _connect_to_drone(self, addr_type, addr):
        try:
            print(f"[BLE] Conectando a {addr_bytes_to_hex(addr)} ...")
            self._ble.gap_connect(addr_type, addr)
        except Exception as e:
            print(f"[BLE] Erro ao conectar: {e}")

    def send_command(self, packet):
        if self._conn_handle is None or self._uart_rx_handle is None:
            return False
        try:
            self._ble.gattc_write(self._conn_handle, self._uart_rx_handle, packet)
            return True
        except Exception as e:
            print(f"[BLE] Erro ao enviar: {e}")
            return False

    def is_connected(self):
        return self._conn_handle is not None and self._uart_rx_handle is not None

    def stop(self):
        self._should_run = False
        try: self._ble.active(False)
        except: pass

# --- IMU ---
i2c = I2C(0, sda=Pin(8), scl=Pin(9))
imu = MPU9250(i2c)

try:
    with open("accel_cal.json") as f:
        calib = ujson.load(f)
    print("[IMU] Calibração carregada:", calib)
except Exception:
    print("[IMU] Arquivo accel_cal.json não encontrado! Usando padrão.")
    calib = {"offset_x": 0, "offset_y": 0, "offset_z": 0, "scale_x": 1, "scale_y": 1, "scale_z": 1}

def calibrate_gyro(samples=200, delay=0.01):
    print("[IMU] Calibrando giroscópio... Mantenha parado!")
    offsets = [0.0, 0.0, 0.0]
    for i in range(samples):
        gx, gy, gz = imu.gyro
        offsets[0] += gx / samples
        offsets[1] += gy / samples
        offsets[2] += gz / samples
        if i % 50 == 0:
            print(f"[IMU] Progresso: {int(i/samples*100)}%")
        time.sleep(delay)
    print(f"[IMU] Gyro calibrado. Offsets: {offsets}")
    return offsets

def process_sensors(ax_raw, ay_raw, az_raw, gx, gy, gz, gyro_offsets):
    ax = (ay_raw - calib["offset_y"]) * calib["scale_y"] / 9.8
    ay = (ax_raw - calib["offset_x"]) * calib["scale_x"] / 9.8
    az = (az_raw - calib["offset_z"]) * calib["scale_z"] / 9.8

    gx -= gyro_offsets[0]
    gy -= gyro_offsets[1]
    gz -= gyro_offsets[2]

    pitch_acc = atan2(ax, az) if az != 0 else 0
    roll_acc = atan2(ay, az) if az != 0 else 0

    pitch_deg = degrees(pitch_acc)
    roll_deg = degrees(roll_acc)

    # --- Normalização para protocolo do drone ---
    def norm2byte(val, neutral=127, dead=10, maxbyte=200, maxval=45):
        # centraliza em neutral, faixa ±maxval → 0-200
        v = int(val * 100 / maxval)
        if abs(v) < dead: return neutral
        elif v < 0: return max(0, neutral + v)
        else: return min(maxbyte, neutral + v)

    roll = norm2byte(roll_deg)
    pitch = norm2byte(pitch_deg)
    # Yaw pelo giroscópio Z
    yaw = norm2byte(gz * 100, neutral=127, dead=5, maxbyte=200, maxval=100)
    # Throttle pelo az (pode ajustar conforme seu gesto)
    throttle = norm2byte(az * 100, neutral=127, dead=5, maxbyte=200, maxval=100)

    return roll, pitch, yaw, throttle

# --- Main ---
async def main():
    ble = bluetooth.BLE()
    controller = BLEGestureController(ble)
    gyro_offsets = calibrate_gyro()
    controller.scan_and_connect(scan_time_ms=30000)

    t_out = time.time() + 35
    while not controller.is_connected():
        print("[MAIN] Aguardando conexão...")
        await asyncio.sleep(1)
        if time.time() > t_out:
            print("[MAIN] Timeout! Não foi possível conectar. Reinicie drone/luva e tente novamente.")
            return

    print("[MAIN] === CONTROLE GESTUAL ATIVO ===")
    print("[MAIN] Gesto: Aceno brusco para CIMA = Switch Take Off/Landing")

    # --- Variáveis do sistema de switch ---
    flight_state = False           # False = no chão, True = voando
    GESTURE_THRESHOLD = 8.0        # sensibilidade do gesto (ajuste conforme necessário)
    GESTURE_COOLDOWN = 20          # mínimo de ciclos (~1s) entre gestos
    COMMAND_DURATION = 8           # ciclos que mantém comando ativo
    
    gesture_cooldown_counter = 0
    action_counter = 0
    current_action = 0
    last_az = 0
    first_reading = True

    try:
        while controller.is_connected():
            ax_raw, ay_raw, az_raw = imu.acceleration
            gx, gy, gz = imu.gyro
            roll_cmd, pitch_cmd, yaw_cmd, throttle_cmd = process_sensors(ax_raw, ay_raw, az_raw, gx, gy, gz, gyro_offsets)

            # Ignora primeira leitura para evitar falso positivo
            if first_reading:
                last_az = az_raw
                first_reading = False
                await asyncio.sleep_ms(50)
                continue

            # --- Detecção do gesto switch ---
            az_delta = az_raw - last_az

            # Gesto: aceno brusco para CIMA (subir rápido a ponta)
            if (az_delta > GESTURE_THRESHOLD and 
                gesture_cooldown_counter == 0 and 
                action_counter == 0):
                
                if not flight_state:
                    print("[GESTURE] TAKE OFF - Switch ativado!")
                    current_action = 24     # comando take off
                    flight_state = True     # atualiza estado: agora está voando
                else:
                    print("[GESTURE] LANDING - Switch ativado!")
                    current_action = 72     # comando landing
                    flight_state = False    # atualiza estado: agora está no chão
                
                action_counter = COMMAND_DURATION
                gesture_cooldown_counter = GESTURE_COOLDOWN

            # --- Mantém comando ativo por alguns ciclos ---
            button = 0
            if action_counter > 0:
                button = current_action
                action_counter -= 1

            # --- Cooldown entre gestos ---
            if gesture_cooldown_counter > 0:
                gesture_cooldown_counter -= 1

            # Atualiza valor anterior para próxima comparação
            last_az = az_raw

            # --- Monta pacote de comando (8 bytes como esperado pelo drone) ---
            packet = bytearray([0, roll_cmd, pitch_cmd, yaw_cmd, throttle_cmd, button, 0, 0])

            success = controller.send_command(packet)
            
            # Log diferenciado para comandos especiais
            if button != 0:
                action_str = "TAKE OFF" if button == 24 else "LANDING"
                state_str = "VOANDO" if flight_state else "NO CHÃO"
                print(f"[MAIN] {action_str}: {list(packet)} | Estado: {state_str}")
            else:
                # Log normal mais limpo (só a cada 10 ciclos para não spammar)
                if gesture_cooldown_counter % 10 == 0:
                    state_str = "VOANDO" if flight_state else "NO CHÃO"
                    print(f"[MAIN] CMD: R={roll_cmd} P={pitch_cmd} Y={yaw_cmd} T={throttle_cmd} | {state_str}")

            await asyncio.sleep_ms(50)  # 20Hz

    except KeyboardInterrupt:
        print("[MAIN] Parando controle gestual...")
        controller.stop()
    except Exception as e:
        print("[MAIN] Erro no loop principal:", e)
        controller.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("[GLOBAL] Erro ao iniciar asyncio:", e)
