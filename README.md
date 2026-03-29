# AeroGlove — PyDrone (ESP32 gesture-controlled drone)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Projeto MicroPython leve para ESP32 que implementa controle gestual de drones (PyDrone). O dispositivo lê uma IMU (MPU6500/MPU9250 + AK8963) e traduz gestos da mão em comandos de voo (throttle, pitch, roll, yaw). Este repositório contém drivers, utilitários BLE e firmware de exemplo para o controlador de voo AeroGlove.

## Principais funcionalidades
- Drivers de IMU: `mpu6500.py`, `mpu9250.py`, `ak8963.py`
- Utilitários BLE e exemplos (arquivos `ble_*`, pasta `lib/aioble`)
- Scripts de entrada: `boot.py`, `main.py`
- Armazenamento de calibração: `accel_cal.json`

## Estrutura do repositório
- `boot.py`, `main.py` — inicialização do dispositivo e loop principal
- `mpu6500.py`, `mpu9250.py`, `ak8963.py` — drivers dos sensores
- `ble_advertising.py`, `ble_simple_peripheral.py` — exemplos BLE
- `lib/aioble/` — biblioteca aioble incluída para exemplos
- `accel_cal.json` — dados de calibração do acelerômetro

## Início rápido — desenvolvimento local

Este repositório é a fonte do projeto PyDrone (trabalho de conclusão). Para começar localmente:

- Clone ou copie o projeto para sua máquina de desenvolvimento.
- Verifique `main.py`, `boot.py` e os drivers de IMU (`mpu6500.py`, `mpu9250.py`, `ak8963.py`) para ajustar a configuração dos sensores e o mapeamento de gestos ao seu hardware.
- Use `mpremote` (ou `ampy`) para transferir os arquivos para o ESP32 (exemplos abaixo).

### Repositório do dispositivo base utilizado:
```bash
https://github.com/01studio-lab/pyDrone
```
## Gravação / implantação no ESP32 (exemplos para PowerShell no Windows)
Recomenda-se usar o `mpremote` (parte do conjunto de ferramentas mpremote). Isso copia os arquivos do repositório para o sistema de arquivos do dispositivo.

```powershell
# AeroGlove 🧤✈️
> Controle Gestual para Drones com ESP32 e MicroPython

Este documento contém apenas instruções passo a passo para que usuários reproduzam os resultados demonstrados pelo projeto AeroGlove. Siga cada etapa com atenção. Não contém dicas de desenvolvimento.

## Resumo do projeto
O AeroGlove é uma luva controladora capaz de pilotar drones por gestos, usando um ESP32 e uma IMU (MPU9250/MPU6500 + AK8963). O firmware é escrito em MicroPython.

## Materiais necessários
- MCU: ESP32-S3 (ou ESP32 padrão)
# AeroGlove 🧤✈️

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Controle Gestual para Drones com ESP32 e MicroPython

Este documento contém apenas instruções passo a passo para que usuários reproduzam os resultados do projeto AeroGlove. Siga cada etapa com atenção. Não contém dicas de desenvolvimento.

## Resumo
O AeroGlove é uma luva controladora que permite pilotar drones por meio de gestos naturais da mão. Utiliza um ESP32 e um módulo IMU (MPU9250/MPU6500 + AK8963). O firmware é escrito em MicroPython.

## Materiais necessários
- MCU: ESP32-S3 (ou ESP32 padrão)
- IMU: Módulo GY-91 (MPU9250 ou MPU6500 + AK8963)
- Bateria LiPo 3.7V e circuito de carregamento (ex.: TP4056)
- Placa de desenvolvimento ou circuito com conectores adequados
- (Opcional) Case impresso em 3D

## Pinagem (exemplo I2C)
- SDA: GPIO 8
- SCL: GPIO 9
- VCC: 3.3V
- GND: GND

Confirme a pinagem no seu hardware antes de alimentar o sistema.

## Preparar o firmware MicroPython
1. Baixe a imagem de firmware MicroPython compatível com o seu modelo de ESP32.
2. Conecte o ESP32 ao computador via USB.
3. No PowerShell (Windows), apague a flash e escreva o firmware (substitua `<firmware.bin>` e `COM3` pelos valores corretos):

```powershell
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 <firmware.bin>
```

Se necessário, instale o esptool com:

```powershell
pip install esptool
```

## Enviar os arquivos do projeto para o dispositivo
Recomenda-se usar o `mpremote` para copiar os arquivos para o ESP32. Substitua `COM3` pela porta correta.

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
1. Coloque a luva com o IMU sobre uma superfície estável em posição neutra.
2. Ligue o dispositivo ou reinicie-o para executar a calibração automática (se implementada).
3. Mantenha a mão imóvel durante o ciclo de calibração (10–15 segundos).
4. Verifique o arquivo `accel_cal.json` no dispositivo para confirmar que os valores foram salvos.

## Verificar sensores (teste rápido)
Abra um REPL (prompt interativo) e execute comandos para confirmar leitura do IMU:

```powershell
mpremote connect serial://COM3 repl
# no prompt do MicroPython
import mpu9250
imu = mpu9250.MPU9250()
print(imu.accel)
```

Se os valores estiverem plausíveis (aproximadamente 0,0,1g no eixo Z em repouso), o sensor está funcionando.

## Procedimento de ensaio em voo (reprodução dos resultados)
AVISO: realize testes em área aberta, com proteção adequada e seguindo normas de segurança. Nas fases iniciais, remova as hélices quando possível.

1. Monte o drone com motores, ESCs e alimentação. Verifique todas as conexões.
2. Ligue o drone e a luva (AeroGlove). Aguarde o estado pronto (LED piscando indica espera por conexão BLE).
3. Emparelhe a luva com o sistema de voo via BLE (LED fica estável quando conectado).
4. No solo, com hélices removidas ou com proteção, execute os testes: inclinar a mão para frente — comando de avanço; inclinar para trás — recuo; inclinações laterais — roll; rotação da mão — yaw.
5. Após validar a correspondência gesto→comando, faça um teste com hélices em baixa altitude e supervisão cuidadosa.

## Indicadores de status
- LED piscando: aguardando conexão BLE
- LED fixo: conectado

## Arquivos principais usados na reprodução
- `main.py` — loop principal e mapeamento de gestos
- `mpu9250.py` / `mpu6500.py` — drivers do IMU
- `ak8963.py` — driver do magnetômetro
- `accel_cal.json` — calibração

## Segurança e boas práticas
- Teste sem hélices nas fases iniciais.
- Use óculos de proteção e mantenha distância segura.
- Verifique a integridade da bateria antes de cada voo.

---
Autor: Thiago Araujo
