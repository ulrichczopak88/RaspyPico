"""
DS18B20 Schnelltest fuer Raspberry Pi Pico (MicroPython).

Ausfuehrung direkt auf dem Pico, z. B.:
mpremote connect auto run ds18b20/ds18b20_test.py
"""

from machine import Pin
import ds18x20
import time


# Daten-Pin fuer den OneWire-Bus.
# Bei anderer Verkabelung hier anpassen (z. B. 14, 16, ...).
DATA_PIN = 2

# Messintervall in Sekunden.
INTERVAL_S = 1.0


# OneWire-Bus am gewaehlten Pin initialisieren.
ow = onewire.OneWire(Pin(DATA_PIN))

# DS18B20-Treiber auf den OneWire-Bus setzen.
ds = ds18x20.DS18X20(ow)

# Nach allen angeschlossenen DS18B20 am Bus suchen.
roms = ds.scan()
print("Gefundene Sensoren:", roms)

if not roms:
    print("Kein DS18B20 gefunden. Verkabelung und 4.7 kOhm Pull-up pruefen.")
    raise SystemExit

print("Starte Messung. Abbruch mit Ctrl+C")

while True:
    # Messung auf allen Sensoren gleichzeitig starten.
    ds.convert_temp()

    # Datenblatt: maximale Wandlungszeit (12 Bit) ca. 750 ms.
    time.sleep_ms(750)

    # Temperaturwerte aller gefundenen Sensoren auslesen.
    for idx, rom in enumerate(roms, start=1):
        temp_c = ds.read_temp(rom)
        print("Sensor", idx, "Temp:", temp_c, "C")

    print("---")
    time.sleep(INTERVAL_S)

