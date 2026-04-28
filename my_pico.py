from dataclasses import dataclass
from time import sleep

import serial.tools.list_ports
from mpremote.transport import TransportError
from mpremote.transport_serial import SerialTransport


@dataclass
class Pico:
    # Kleine Huelle um die serielle Verbindung zum Pico.
    transport: SerialTransport
    data_pin: int = 2
    ds18b20_resolution: int = 10
    sensor_ready: bool = False
    led_ready: bool = False

    def close(self):
        # Verbindung sauber schliessen, wenn sie nicht mehr gebraucht wird.
        if self.transport.in_raw_repl:
            self.transport.exit_raw_repl()
        self.transport.close()


def _exec(pico, code):
    # Kleiner Schutz fuer laengere Live-Sessions:
    # Falls der Raw-REPL-Zustand verloren geht, einmal neu betreten und wiederholen.
    try:
        if not pico.transport.in_raw_repl:
            pico.transport.enter_raw_repl(soft_reset=False)
        return pico.transport.exec(code)
    except TransportError:
        pico.transport.in_raw_repl = False
        pico.transport.enter_raw_repl(soft_reset=False)
        return pico.transport.exec(code)


def _find_auto_port():
    # Gleiches Prinzip wie "mpremote connect auto":
    # den ersten gefundenen USB-Seriell-Port verwenden.
    for port in sorted(serial.tools.list_ports.comports()):
        if port.vid is not None and port.pid is not None:
            return port.device
    raise RuntimeError("Kein Pico gefunden. Ist er per USB verbunden?")


def connect(device="auto", data_pin=2, ds18b20_resolution=10):
    """Verbindung zum Pico aufbauen und fuer schnelle Befehle vorbereiten."""
    if device == "auto":
        device = _find_auto_port()
    elif device.startswith("port:"):
        device = device.removeprefix("port:")

    transport = SerialTransport(device, baudrate=115200)

    # Raw REPL ist der schnelle Befehlsmodus von MicroPython.
    # soft_reset=False laesst den Pico-Zustand moeglichst unveraendert.
    transport.enter_raw_repl(soft_reset=False)
    return Pico(
        transport=transport,
        data_pin=data_pin,
        ds18b20_resolution=ds18b20_resolution,
    )


def _ds18b20_config(resolution):
    # DS18B20-Aufloesung:
    # 9 Bit ist am schnellsten, 12 Bit am genauesten.
    configs = {
        9: 0x1F,
        10: 0x3F,
        11: 0x5F,
        12: 0x7F,
    }
    if resolution not in configs:
        raise ValueError("ds18b20_resolution muss 9, 10, 11 oder 12 sein")
    return configs[resolution]


def _setup_sensor(pico):
    # Sensor-Objekte einmal auf dem Pico anlegen und das ROM merken.
    config = _ds18b20_config(pico.ds18b20_resolution)
    code = f"""
from machine import Pin
import onewire, ds18x20
_ow = onewire.OneWire(Pin({pico.data_pin}))
_ds = ds18x20.DS18X20(_ow)
_roms = _ds.scan()
if not _roms:
    raise Exception("Kein DS18B20 Sensor an GP{pico.data_pin} gefunden")
_rom = _roms[0]
_ow.reset()
_ow.select_rom(_rom)
_ow.writebyte(0x4E)
_ow.writebyte(75)
_ow.writebyte(70)
_ow.writebyte({config})
"""
    _exec(pico, code)
    pico.sensor_ready = True


def get_temp(pico, wait=0.75):
    """Aktuelle Temperatur in Grad Celsius lesen."""
    if not pico.sensor_ready:
        _setup_sensor(pico)

    # convert_temp() startet eine neue Messung.
    # Der DS18B20 braucht danach kurz Zeit, sonst kommt kein neuer Wert.
    _exec(pico, "_ds.convert_temp()")
    sleep(wait)

    output = _exec(pico, "print(_ds.read_temp(_rom))")
    return float(output.decode().strip())


def get_internal_temp(pico):
    """Interne RP2040-Temperatur in Grad Celsius lesen."""
    code = """
from machine import ADC
_internal_sensor = ADC(4)
_raw = _internal_sensor.read_u16()
_voltage = _raw * 3.3 / 65535
_temp_c = 27 - (_voltage - 0.706) / 0.001721
print(_temp_c)
"""
    output = _exec(pico, code)
    return float(output.decode().strip())


def get_temps(pico, wait=0.2):
    """DS18B20 und interne Pico-Temperatur gemeinsam lesen."""
    if not pico.sensor_ready:
        _setup_sensor(pico)

    # Messung, kurze Wartezeit und beide Temperaturen in einem Pico-Aufruf.
    code = f"""
from machine import ADC
import time
_ds.convert_temp()
time.sleep({float(wait)})
_internal_sensor = ADC(4)
_raw = _internal_sensor.read_u16()
_voltage = _raw * 3.3 / 65535
_internal_temp = 27 - (_voltage - 0.706) / 0.001721
print(str(_ds.read_temp(_rom)) + "," + str(_internal_temp))
"""
    output = _exec(pico, code).decode().strip()
    ds18b20_temp, internal_temp = output.split(",")
    return float(ds18b20_temp), float(internal_temp)


def _setup_led(pico):
    # Beim Pico ist die Board-LED normalerweise auf dem Pin "LED".
    _exec(pico, "from machine import Pin\n_led = Pin('LED', Pin.OUT)")
    pico.led_ready = True


def set_led(pico, on=True):
    """Board-LED ein- oder ausschalten."""
    if not pico.led_ready:
        _setup_led(pico)
    value = 1 if on else 0
    _exec(pico, f"_led.value({value})")
    return bool(value)


def get_led(pico):
    """Aktuellen Zustand der Board-LED lesen."""
    if not pico.led_ready:
        _setup_led(pico)
    output = _exec(pico, "print(_led.value())")
    return bool(int(output.decode().strip()))


def toggle_led(pico):
    """Board-LED umschalten und neuen Zustand zurueckgeben."""
    if not pico.led_ready:
        _setup_led(pico)
    output = _exec(pico, "_led.value(0 if _led.value() else 1)\nprint(_led.value())")
    return bool(int(output.decode().strip()))


def disconnect(pico):
    """Kurzer Alias, falls du lieber my_pico.disconnect(pico) schreibst."""
    pico.close()
