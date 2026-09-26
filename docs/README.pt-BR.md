<div align="center">
  <a href="#root"><img src="./banner.svg?v=2" alt="AeroGlove" width="100%"/></a>
</div>

> 🇺🇸 [English version](../README.md)

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <pre lang="bash"><code>$ aeroglove / briefing
----------------------------------------------
• drone    : pyDrone quad-X microdrone
• entrada  : atitude da mão, IMU na luva
• sensor   : GY-91 · MPU-9250 9-DOF + BMP280
• canais   : THR / ROLL / PITCH / YAW (µs)
• shaping  : deadband 0.02 · expo 0.3 · ±30° FS
• pacote   : 14 B binário @ 100 Hz, ESP-NOW</code></pre>
    </td>
    <td width="50%" valign="top">
      <pre lang="python"><code>class Luva:
    fusao    = MadgwickAHRS(beta=0.08)  # 100 Hz
    link     = "esp-now | ble-nus fallback"
    failsafe = "corta motores > 200 ms mudo"
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

### ❯ o_que_e

O AeroGlove é uma luva controladora vestível que pilota um quadcóptero com
gestos da mão. Um ESP32-S3 rodando MicroPython lê uma IMU GY-91 (MPU-9250
9-DOF com barômetro BMP280) via I2C a 400 kHz, funde a orientação com Madgwick
AHRS a 100 Hz (β = 0.08), converte a atitude da mão nos quatro canais RC
(throttle, roll, pitch, yaw) com deadband e curva exponencial, e transmite
pacotes binários de 14 bytes via ESP-NOW para o receptor no drone. Um link BLE
NUS serve de fallback. Se o receptor ficar mais de 200 ms sem pacotes, ele
corta os motores.

A plataforma de voo alvo é o [pyDrone](https://github.com/01studio-lab/pyDrone)
quad-X da 01Studio.

---

### ❯ cadeia_de_sinal

<div align="center">
  <img src="./architecture.svg?v=2" alt="Cadeia de sinal do AeroGlove" width="100%"/>
</div>

Da mão à hélice, uma iteração do loop:

1. **Amostragem:** leitura de aceleração, velocidade angular e pressão
   barométrica do GY-91 via I2C a 400 kHz.
2. **Fusão:** o `MadgwickAHRS` integra quatérnios a 100 Hz com β = 0.08,
   elimina o drift do giroscópio e produz os ângulos de roll, pitch e yaw.
3. **Mapeamento:** inclinação frontal/traseira controla o pitch, inclinação
   lateral controla o roll e a rotação do punho controla o yaw. Deadband de
   0.02 zera o jitter no centro e a curva expo (0.3) suaviza a resposta;
   fundo de escala em torno de ±30°.
4. **Transmissão:** os canais são empacotados em um frame fixo de 14 bytes
   (sequência, quatro canais u16, temperatura, reservado) e enviados por
   ESP-NOW a cada 10 ms. Latência de ar abaixo de 10 ms; cliente BLE NUS
   como fallback.
5. **Failsafe:** o receptor decodifica os canais para o mixer dos 4 motores
   e roda um watchdog: mais de 200 ms sem pacote e os motores desligam.

---

### ❯ hardware

| Componente | Especificação recomendada | Função |
| :--- | :--- | :--- |
| MCU | ESP32-S3 dual-core (ou ESP32 padrão) | Processamento na luva e no drone |
| IMU | Módulo GY-91 (MPU-9250 + BMP280) | Giroscópio, acelerômetro, magnetômetro, barômetro |
| Bateria da luva | LiPo 3.7 V (500-1200 mAh) | Alimentação autônoma |
| Carregador | Módulo TP4056 com proteção | Carga via USB-C / micro-USB |
| Estrutura vestível | Luva esportiva/têxtil + case impresso em 3D | Fixação da eletrônica na mão |
| Aeronave | Microdrone quad-X | Plataforma de voo ([pyDrone 01Studio](https://github.com/01studio-lab/pyDrone)) |

---

### ❯ pinagem

Ligue o GY-91 ao barramento I2C do ESP32:

```
  Módulo GY-91               ESP32 / ESP32-S3
 ┌──────────────┐            ┌──────────────────┐
 │     VCC      │───────────▶│  3.3V            │
 │     GND      │───────────▶│  GND             │
 │     SDA      │───────────▶│  GPIO 8  (I2C)   │
 │     SCL      │───────────▶│  GPIO 9  (I2C)   │
 └──────────────┘            └──────────────────┘
```

> Confirme a pinagem da sua placa e o nível de tensão (3.3 V) antes de energizar.

---

### ❯ gravar_e_voar

**1. Gravar o MicroPython no ESP32**

```bash
pip install esptool

# apagar a flash
esptool.py --chip esp32s3 --port COM3 erase_flash

# gravar o binário do MicroPython
esptool.py --chip esp32s3 --port COM3 write_flash -z 0x0 <firmware.bin>
```

Use a porta serial correta (`COM3` no Windows, `/dev/ttyUSB0` no Linux).

**2. Enviar os arquivos com mpremote**

```bash
pip install mpremote
mpremote list

# arquivos do transmissor (luva)
mpremote connect COM3 fs cp controller/espnow_tx.py :main.py
mpremote connect COM3 fs cp controller/imu_madgwick.py :imu_madgwick.py
mpremote connect COM3 fs cp controller/gy91.py :gy91.py
mpremote connect COM3 fs cp controller/mpu925x.py :mpu925x.py
mpremote connect COM3 fs cp controller/bmp280_min.py :bmp280_min.py
mpremote connect COM3 fs cp controller/ble_nus_client.py :ble_nus_client.py

mpremote connect COM3 run "import machine; machine.reset()"
```

**3. Calibrar a posição neutra da IMU**

1. Apoie a luva numa superfície plana e estável, com a mão aberta em posição neutra.
2. Ligue a placa (ou rode o script de calibração).
3. Mantenha a mão imóvel por 10-15 s para o filtro Madgwick convergir o vetor
   de gravidade (1.0 g no eixo Z).

**4. Teste rápido no REPL**

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

### ❯ teste_de_bancada

> **Aviso de segurança: faça os primeiros testes sempre com as hélices
> removidas**, ou numa bancada protegida.

1. Verificação de hardware: aperto dos motores, conexões de alimentação e
   carga da LiPo.
2. Pareamento: ligue a luva e o drone; o LED de status indica a
   sincronização do link ESP-NOW/BLE.
3. Teste de bancada (sem hélices):
   - Incline a mão para frente → os motores traseiros aceleram (pitch down / avanço).
   - Incline a mão para a direita → os motores do lado esquerdo compensam (roll right).
   - Gire o punho no sentido horário → os pares diagonais respondem (yaw CW).
4. Teste de voo: com as hélices instaladas, comece em área aberta e plana
   com pequenos saltos em baixa altitude para validar a estabilidade.

---

### ❯ mapa_do_repo

<pre lang="text"><code>controller/                  firmware transmissor da luva (AeroGlove)
  ├── espnow_tx.py           loop principal, envio ESP-NOW @ 100 Hz
  ├── imu_madgwick.py        filtro de orientação Madgwick AHRS
  ├── gy91.py                driver composto do GY-91 (9-DOF + baro)
  ├── mpu925x.py             driver minimalista MPU-9250 / MPU-9255
  ├── bmp280_min.py          driver barométrico BMP280
  ├── ble_nus_client.py      cliente fallback BLE Nordic UART
  └── test_gy91_madgwick.py  testes de convergência e calibração
drone/                       firmware receptor na aeronave
  └── espnow_rx.py           RX ESP-NOW, decode 4CH, failsafe de 200 ms
docs/                        banner.svg · architecture.svg · README.pt-BR.md</code></pre>

---

### ❯ referencias

- Plataforma base: [pyDrone (01studio-lab)](https://github.com/01studio-lab/pyDrone)
- Fusão sensorial: Madgwick, S. O. (2010), *An efficient orientation filter for
  inertial and inertial/magnetic sensor arrays*

---

Desenvolvido por **Thiago Araújo** ([@thisux1](https://github.com/thisux1)).
Distribuído sob a [Licença MIT](../LICENSE).
