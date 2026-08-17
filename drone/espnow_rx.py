import network
import espnow
import time


def main():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    e = espnow.ESPNow()
    e.active(True)

    last = time.ticks_ms()
    while True:
        host, msg = e.recv()
        now = time.ticks_ms()
        if msg:
            # decode channels
            def r16(i):
                return (msg[i] << 8) | msg[i + 1]
            seq = r16(0)
            ch_thr = r16(2)
            ch_roll = r16(4)
            ch_pitch = r16(6)
            ch_yaw = r16(8)
            # placeholder: print; integrar mixer/ESC depois
            print("seq", seq, ch_thr, ch_roll, ch_pitch, ch_yaw)
            last = now
        # failsafe se >200ms sem pacote
        if time.ticks_diff(now, last) > 200:
            # aqui cortar/atenuar motores; por enquanto apenas log
            # print("failsafe")
            last = now
        time.sleep_ms(5)


if __name__ == "__main__":
    main()


