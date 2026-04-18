#!/usr/bin/env python3
import time
import numpy as np
from scipy.signal import butter, filtfilt
import Adafruit_ADS1x15
import sys

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token="putYourInfluxDBtokenHere"
org = "firstInfluxDBOrg"
url = "http://127.0.0.1:8086"
bucket = "yourSensorBucketGouesHere"
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)


# ----------------------------------------------------
# ADS1115 Setup (SM-6/V2 Geophon)
# ----------------------------------------------------
ads = Adafruit_ADS1x15.ADS1115(address=0x49, busnum=1)
GAIN = 16  # ±0.256 V

# Geophon-Kalibrierung
GEOPHON_SENSITIVITY = 28.8  # V/(m/s)

# Filterparameter
FS = 500
LOWCUT = 5
HIGHCUT = 150

# Deine Werte
ALARM_THRESHOLD = 0.0299
HYSTERESIS_RESET = 0.005
COOLDOWN = 1.75
last_alarm_time = 0

# Erfassungsdauer
CAPTURE_DURATION = 10.0  # Sekunden

# ----------------------------------------------------
def on_alarm(max_value, rms_value, duration):
    print("=== Erschütterung registriert: ===", flush=True)
    print(f"Maximalwert: {max_value:.4f} mm/s", flush=True)
    print(f"RMS-Wert:    {rms_value:.4f} mm/s", flush=True)
    print(f"Dauer:       {duration:.2f} Sekunden", flush=True)
    print("================", flush=True)
    point = (
    Point("SM6V263002_Geophone")
#    .tag("tagname1", "tagvalue1")
    .field("Max", max_value)
    .field("RMS", rms_value)
    .field("Duration", duration)
    )
    write_api.write(bucket=bucket, org="zeropi", record=point)

# ----------------------------------------------------
def bandpass_filter(data, fs=FS, low=LOWCUT, high=HIGHCUT):
    nyq = 0.5 * fs
    low /= nyq
    high /= nyq
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, data)

# ----------------------------------------------------
def main():
    global last_alarm_time
    buffer = []

    capturing = False
    capture_start = 0
    capture_values = []

    print("Geophon-Überwachung gestartet (mit 8s Capture)", flush=True)

    while True:
        # -----------------------------
        # Rohmessung
        # -----------------------------
        raw = ads.read_adc_difference(0, gain=GAIN)
        voltage = raw * 0.0000078125
        velocity_mm_s = (abs(voltage) / GEOPHON_SENSITIVITY) * 1000
        value = velocity_mm_s * 10

        # -----------------------------
        # Bandpass
        # -----------------------------
        buffer.append(value)
        if len(buffer) > 500:
            buffer.pop(0)

        if len(buffer) > 50:
            try:
                filtered = bandpass_filter(buffer)
                value = filtered[-1]
            except:
                pass

        now = time.time()

        # -----------------------------
        # Cooldown aktiv?
        # -----------------------------
        if (now - last_alarm_time) < COOLDOWN:
            time.sleep(0.2)
            continue

        # -----------------------------
        # Capture starten?
        # -----------------------------
        if not capturing:
            if (value >= ALARM_THRESHOLD) or (value <= -ALARM_THRESHOLD):
                capturing = True
                capture_start = now
                capture_values = [value]
                continue

        # -----------------------------
        # Capture läuft
        # -----------------------------
        if capturing:
            capture_values.append(value)

            # Ende wenn 8 Sekunden vorbei
            if (now - capture_start) >= CAPTURE_DURATION:
                capturing = False

            # Ende wenn Wert wieder unter Hysterese
            if abs(value) < HYSTERESIS_RESET:
                capturing = False

            # Wenn Capture endet → Alarm auslösen
            if not capturing:
                duration = now - capture_start
                max_value = max(abs(v) for v in capture_values)
                rms_value = np.sqrt(np.mean(np.square(capture_values)))

                on_alarm(max_value, rms_value, duration)
                last_alarm_time = now

        time.sleep(0.2)

# ----------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
