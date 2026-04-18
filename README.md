# GeoMon - An Affordable Geophone Monitoring System (SM‑6/V2 + ADS1115)

## DIN‑4150 oriented vibration monitoring with real‑time filtering, RMS/peak analytics, event capture, hysteresis, cooldown logic, and InfluxDB time‑series logging

This project implements a precise, real‑time vibration monitoring system based on an **SM‑6/V2 geophone** and an **ADS1115 ADC**.  
The focus is on **DIN‑4150‑aligned measurement**, stable event detection, and clean data recording for long‑term analysis.

---

## 🚧 Hardware

### Geophone (SM‑6/V2)
- Resonant frequency: 4.5 Hz  
- Sensitivity: 28.8 V/(m/s)  
- Coil resistance: 375 Ω  
- Behavior: underdamped, typical ringing 3–8 s  

### ADC (ADS1115)
- Resolution: 16‑bit  
- Gain: ±0.256 V (GAIN=16)  
- LSB: 7.8125 µV  
- I²C interface  

---

## 🧠 Signal Processing

### 1. Calibration (ADC → velocity)
Conversion is based on the known geophone sensitivity:

v_mm_s = (U_volts / 28.8) * 1000

Optional scaling factor (e.g., ×10) for better visibility.

### 2. Band‑pass filter
Butterworth 4th order:

- Standard: **5–200 Hz**
- Optional: **8–150 Hz** (reduces ringing)

Switchable via constant:
USE_TIGHTER_BANDPASS = True/False


### 3. Threshold & hysteresis logic
- Primary threshold: `ALARM_THRESHOLD = 0.0999` mm/s  
- Bidirectional:  
  `value >= threshold` **or** `value <= -threshold`
- Optional:  
  `USE_HYSTERESIS = True`  
  `HYSTERESIS_RESET = 0.05` mm/s  

### 4. Cooldown phase
After each event:
COOLDOWN = 5.5  # seconds

No new triggers during cooldown.

### 5. Event recording (8‑second capture)
When the threshold is exceeded:

1. Immediate start of recording  
2. Collect all filtered values for exactly 8 seconds  
3. Automatic stop after timeout or hysteresis reset  
4. Compute:
   - Peak (mm/s)
   - RMS (mm/s)
   - Duration (s)
5. Output a structured event  
6. Cooldown begins  

---

## 🔧 Anti‑ringing options

**Software:**
- Tighter band‑pass (8–150 Hz)
- Hysteresis

**Hardware:**
- 1–2 kΩ shunt resistor to increase damping  
  (Note: sensitivity decreases)

---

## 🖥️ Systemd Integration

### Script path

/usr/local/bin/geophone_monitor.py

### Service file

/etc/systemd/system/geophone-monitor.service

### Important commands

sudo systemctl start geophone-monitor
sudo systemctl enable geophone-monitor
sudo systemctl status geophone-monitor
sudo journalctl -u geophone-monitor -f


---

## 📡 InfluxDB Integration (Time‑Series Logging)

The system can write measurements and events directly into **InfluxDB**.

### Example configuration
```python
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_TOKEN"
INFLUX_ORG = "YOUR_ORG"
INFLUX_BUCKET = "geophone"
```


### Writing a measurement point
```python
point = (
    Point("geophone")
    .field("value", float(value))
    .field("rms", float(rms))
    .field("fft_peak", float(fft_peak))
    .time(datetime.utcnow(), WritePrecision.NS)
)
write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
```

### 📊 Feature Overview

ADS1115 geophone acquisition

SM‑6/V2 calibration (mm/s)

Real‑time band‑pass filtering

Optional tighter filter

Bidirectional threshold detection

Optional hysteresis

8‑second event capture

Peak analysis

RMS analysis

Event duration

Cooldown mechanism

Systemd service

InfluxDB logging

Optional anti‑ringing

### 📝 Summary
This project provides a robust, DIN‑4150‑oriented vibration monitoring system with precise geophone calibration, intelligent event detection, clean filtering, and optional long‑term recording via InfluxDB.
Ideal for structural monitoring, machine diagnostics, environmental vibration analysis, and mini‑seismology.


