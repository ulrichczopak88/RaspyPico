from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import streamlit as st


# Projektordner importierbar machen, damit "import my_pico" immer klappt.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import my_pico


def require_state_defaults():
    # Session-State wird von Streamlit zwischen Reruns behalten.
    st.session_state.setdefault("pico", None)
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("led_on", False)
    st.session_state.setdefault("ds18b20_values", [])
    st.session_state.setdefault("internal_values", [])
    st.session_state.setdefault("times", [])
    st.session_state.setdefault("start_time", time.time())
    st.session_state.setdefault("last_message", "")


def reset_measurements():
    st.session_state.ds18b20_values = []
    st.session_state.internal_values = []
    st.session_state.times = []
    st.session_state.start_time = time.time()
    st.session_state.last_message = ""


def connect_pico(port, data_pin, resolution):
    # Alte Verbindung schliessen, falls schon eine offen war.
    disconnect_pico(clear_message=False)

    st.session_state.pico = my_pico.connect(
        port,
        data_pin=data_pin,
        ds18b20_resolution=resolution,
    )
    st.session_state.led_on = my_pico.get_led(st.session_state.pico)
    st.session_state.running = False
    reset_measurements()
    st.session_state.last_message = "Pico verbunden."


def disconnect_pico(clear_message=True):
    # Verbindung sauber trennen und lokale Steuerwerte zuruecksetzen.
    pico = st.session_state.get("pico")
    if pico is not None:
        try:
            my_pico.disconnect(pico)
        except Exception:
            pass
    st.session_state.pico = None
    st.session_state.running = False
    st.session_state.led_on = False
    if clear_message:
        st.session_state.last_message = "Verbindung getrennt."


def set_led(on):
    pico = st.session_state.pico
    if pico is None:
        return
    st.session_state.led_on = my_pico.set_led(pico, on)


def show_charts(max_points):
    # Die Plots stehen bewusst untereinander, damit beide gut lesbar bleiben.
    plot_times = st.session_state.times[-int(max_points) :]
    ds18b20_values = st.session_state.ds18b20_values[-int(max_points) :]
    internal_values = st.session_state.internal_values[-int(max_points) :]

    st.subheader("DS18B20")
    if ds18b20_values:
        show_temperature_plot(
            plot_times,
            ds18b20_values,
            ylabel="DS18B20 [degC]",
            color="#e4572e",
        )
    else:
        st.info("Noch keine DS18B20-Messwerte.")

    st.subheader("Interne Pico-Temperatur")
    if internal_values:
        show_temperature_plot(
            plot_times,
            internal_values,
            ylabel="Intern [degC]",
            color="#2878b5",
        )
    else:
        st.info("Noch keine internen Messwerte.")


def show_temperature_plot(times, values, ylabel, color):
    # Matplotlib ist hier robuster als st.line_chart, weil wir Achsen und Linie
    # selbst kontrollieren koennen.
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(times, values, marker="o", markersize=3, linewidth=2, color=color)
    ax.set_xlabel("Zeit [s]")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)

    if len(values) == 1:
        ax.set_xlim(max(0, times[0] - 1), times[0] + 1)
    else:
        ax.set_xlim(min(times), max(times))

    ymin = min(values)
    ymax = max(values)
    margin = max(0.5, (ymax - ymin) * 0.2)
    ax.set_ylim(ymin - margin, ymax + margin)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)


def take_live_sample(delay_s, max_samples):
    pico = st.session_state.pico
    if pico is None:
        st.session_state.running = False
        return

    if len(st.session_state.ds18b20_values) >= int(max_samples):
        st.session_state.running = False
        st.session_state.last_message = "Messung beendet."
        return

    loop_start = time.time()

    try:
        # Der DS18B20 braucht je nach Aufloesung Messzeit.
        # Bei 10 Bit sind 0.2 s ein guter schneller Wert.
        wait_s = max(0.05, min(float(delay_s), 0.75))
        ds18b20_temp, internal_temp = my_pico.get_temps(pico, wait=wait_s)
    except Exception as exc:
        st.session_state.running = False
        st.session_state.last_message = f"Messung fehlgeschlagen: {exc}"
        return

    st.session_state.times.append(time.time() - st.session_state.start_time)
    st.session_state.ds18b20_values.append(ds18b20_temp)
    st.session_state.internal_values.append(internal_temp)
    st.session_state.last_message = (
        f"DS18B20={ds18b20_temp:.3f} degC, intern={internal_temp:.3f} degC"
    )

    # Bis zum naechsten Livestream-Takt warten, dann neu rendern.
    rest_s = float(delay_s) - (time.time() - loop_start)
    if rest_s > 0:
        time.sleep(rest_s)
    st.rerun()


st.set_page_config(page_title="Pico Live Temperature", layout="wide")
require_state_defaults()

st.title("Raspberry Pi Pico - Live Temperatur")
st.caption("DS18B20, interne RP2040-Temperatur und Board-LED")

port = st.sidebar.text_input("Port", value="auto")
data_pin = st.sidebar.number_input("DS18B20 GPIO", min_value=0, max_value=28, value=2, step=1)
resolution = st.sidebar.select_slider("DS18B20 Aufloesung", options=[9, 10, 11, 12], value=10)
delay_s = st.sidebar.number_input(
    "Messintervall [s]",
    min_value=0.2,
    max_value=60.0,
    value=0.2,
    step=0.1,
)
num_samples = st.sidebar.number_input(
    "Messpunkte",
    min_value=1,
    max_value=10000,
    value=300,
    step=10,
)
max_points = st.sidebar.number_input(
    "Punkte im Plot",
    min_value=10,
    max_value=2000,
    value=300,
    step=10,
)

is_connected = st.session_state.pico is not None

connect_col, led_col, run_col = st.columns(3)

with connect_col:
    if st.button("Verbinden", disabled=st.session_state.running, use_container_width=True):
        try:
            connect_pico(port, int(data_pin), int(resolution))
            st.rerun()
        except Exception as exc:
            st.session_state.pico = None
            st.session_state.running = False
            st.session_state.last_message = f"Verbindung fehlgeschlagen: {exc}"

    if st.button("Trennen", disabled=not is_connected, use_container_width=True):
        disconnect_pico()
        st.rerun()

with led_col:
    led_a, led_b = st.columns(2)
    with led_a:
        if st.button("LED ein", disabled=not is_connected, use_container_width=True):
            try:
                set_led(True)
            except Exception as exc:
                st.session_state.last_message = f"LED ein fehlgeschlagen: {exc}"
    with led_b:
        if st.button("LED aus", disabled=not is_connected, use_container_width=True):
            try:
                set_led(False)
            except Exception as exc:
                st.session_state.last_message = f"LED aus fehlgeschlagen: {exc}"

    st.metric("LED", "Ein" if st.session_state.led_on else "Aus")

with run_col:
    start_disabled = not is_connected or st.session_state.running
    stop_disabled = not st.session_state.running

    if st.button("Messung starten", disabled=start_disabled, use_container_width=True):
        st.session_state.running = True
        st.session_state.last_message = "Messung laeuft."
        st.rerun()

    if st.button("Messung stoppen", disabled=stop_disabled, use_container_width=True):
        st.session_state.running = False
        st.session_state.last_message = "Messung gestoppt."

    if st.button("Messwerte loeschen", disabled=st.session_state.running, use_container_width=True):
        reset_measurements()
        st.rerun()

if st.session_state.last_message:
    if "fehlgeschlagen" in st.session_state.last_message:
        st.error(st.session_state.last_message)
    else:
        st.success(st.session_state.last_message)
elif not is_connected:
    st.info("Pico per USB verbinden und dann auf 'Verbinden' klicken.")

st.metric("Messpunkte", len(st.session_state.ds18b20_values))
show_charts(max_points)

if st.session_state.running:
    take_live_sample(delay_s, num_samples)
