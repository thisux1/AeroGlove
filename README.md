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

## Quickstart — getting started (local development)

This repository is provided as the final-year PyDrone project source. To get started locally:

- Clone or copy the project to your development machine.
- Inspect `main.py`, `boot.py`, and the IMU drivers (`mpu6500.py`, `mpu9250.py`, `ak8963.py`) to configure sensors and gesture mappings for your hardware.
- Use `mpremote` (or `ampy`) to flash files to your ESP32 (examples below).

Notes
- Do not commit device credentials, private keys, or Wi‑Fi passwords. Keep any sensitive files locally and add them to `.gitignore`.

## Flashing / deploying to the ESP32 (Windows PowerShell examples)
Recommended: use `mpremote` (part of the mpremote toolchain). This copies the repository files to the device filesystem.

```powershell
# AeroGlove 🧤✈️
> Controle Gestual para Drones com ESP32 e MicroPython

Este documento contém apenas instruções passo a passo para que usuários reproduzam os resultados demonstrados pelo projeto AeroGlove. Siga cada etapa com atenção. Não contém dicas de desenvolvimento.

## Resumo do projeto
O AeroGlove é uma luva controladora capaz de pilotar drones por gestos, usando um ESP32 e uma IMU (MPU9250/MPU6500 + AK8963). O firmware é escrito em MicroPython.

## Materiais necessários
- MCU: ESP32-S3 (ou ESP32 padrão)
- IMU: Módulo GY-91 (MPU9250 ou MPU6500 + AK8963)
- Bateria LiPo 3.7V e circuito de carregamento (ex.: TP4056)
- Placa de desenvolvimento ou circuito com conectores adequados
- (Opcional) Impressão 3D do case

## Pinagem (I2C - exemplo)
- SDA: GPIO 8
- SCL: GPIO 9
- VCC: 3.3V
- GND: GND

Confirme a pinagem no seu hardware antes de alimentar o sistema.

## Preparar o firmware MicroPython
1. Baixe a imagem de firmware MicroPython compatível com seu modelo de ESP32 (por exemplo, a imagem oficial para ESP32/ESP32-S3).
2. Conecte o ESP32 ao computador via USB.
3. No PowerShell (Windows), apague a flash e grave o firmware (substitua `<firmware.bin>` pelo nome do arquivo que você baixou e `COM3` pela porta correta):

```powershell
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 <firmware.bin>
```

Observação: se você não tiver `esptool.py`, instale com `pip install esptool`.

## Enviar o firmware e arquivos do projeto para o dispositivo
Recomenda-se usar `mpremote` para copiar os arquivos do repositório para o ESP32. Substitua `COM3` pela porta correta.

```powershell
# listar dispositivos conectados
mpremote list

# enviar o arquivo principal
mpremote connect serial://COM3 fs put main.py /

# enviar a pasta de bibliotecas (se existir)
mpremote connect serial://COM3 fs put lib/ /lib

# enviar arquivo de calibração
mpremote connect serial://COM3 fs put accel_cal.json /

# reiniciar o dispositivo
mpremote connect serial://COM3 run "import machine; machine.reset()"
```

Alternativa: use a IDE Thonny para enviar os arquivos via interface gráfica.

## Calibração do IMU
1. Coloque a luva/lógica com o IMU sobre uma superfície estável numa posição neutra.
2. Ligue o dispositivo ou reinicie-o para que o procedimento de calibração automática (se implementado) seja executado.
3. Mantenha a mão/parada imóvel durante o ciclo de calibração (10–15 segundos).
4. Verifique o arquivo `accel_cal.json` no dispositivo para confirmar que os valores de calibração foram gravados (se aplicável).

## Verificar sensores (teste rápido)
Abra um REPL e execute comandos para confirmar leitura do IMU (exemplo genérico):

```powershell
mpremote connect serial://COM3 repl
# no REPL do MicroPython
import mpu9250
imu = mpu9250.MPU9250()
print(imu.accel)
```

Se receber valores plausíveis (próximos de 0,0,1g em repouso para o eixo Z), o sensor está funcionando.

## Procedimento de ensaio em voo (reprodução dos resultados)
AVISO: realize testes de voo em área aberta, com proteção e seguindo normas de segurança. Retire hélices para testes iniciais quando possível.

1. Monte o drone com motores, ESCs e alimentação. Verifique conexões.
2. Ligue o drone e a luva (AeroGlove). Aguarde até que a luva indique estado pronto (LED piscando para aguardar conexão BLE).
3. Emparelhe a luva com o sistema de voo do drone via BLE (o LED deve ficar estável quando conectado).
4. No solo, com hélices removidas ou com proteção, faça o teste de comandos: incline a mão para frente — verifique se o drone recebe comando de avanço; incline para trás — comando de recuo; inclinações laterais — comandos de roll; movimentos de rotação da mão — yaw.
5. Ao validar a correspondência gesto→comando, prossiga para um teste com hélices e baixa altitude, com retenção manual do drone para verificar resposta de controle.

## Indicadores de status
- LED piscando: aguardando conexão BLE
- LED fixo: conectado ao drone

## Arquivos principais usados na reprodução
- `main.py` — loop principal e mapeamento de gestos
- `mpu9250.py` / `mpu6500.py` — drivers do IMU
- `ak8963.py` — driver do magnetômetro (se aplicável)
- `accel_cal.json` — calibração

## Segurança e boas práticas
- Teste sem hélices nas fases iniciais.
- Use óculos de proteção e mantenha distância segura.
- Verifique a integridade da bateria antes de cada voo.

---
Autor: Thiago Araujo
