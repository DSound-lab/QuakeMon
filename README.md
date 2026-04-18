# QuakeMon -  Geophone Monitoring System (SM-6/V2 + ADS1115)
## DIN-4150 compliant vibration monitoring with filtering, event capture, RMS analysis, hysteresis, and cooldown
Geophone Monitoring System (SM-6/V2 + ADS1115)
DIN-4150 compliant vibration monitoring with filtering, event capture, RMS analysis, hysteresis, and cooldown

This project implements a professional-grade vibration monitoring system using an SM-6/V2 geophone (4.5 Hz, 28.8 V/m/s) connected to an ADS1115 ADC. It runs as a systemd background service and performs real-time vibration analysis, including calibrated velocity measurement (mm/s), bandpass filtering, threshold detection, 8-second event capture, RMS and peak analysis, hysteresis, cooldown logic, and optional anti-ringing features.

1. Hardware

Geophone
- Model: SM-6/V2 (EG-4.5-H)
- Resonant frequency: 4.5 Hz
- Sensitivity: 28.8 V/(m/s)
- Coil resistance: 375 Ω
- Known behavior: underdamped, rings for 3–8 seconds after excitation

ADC
- ADS1115 (I²C)
- Gain: ±0.256 V (GAIN=16)
- Resolution: 7.8125 µV/LSB

2. Signal Processing Pipeline

Calibration (voltage → velocity)
v_mm/s = |U| / 28.8 × 1000

Scaling
A factor of 10× is applied to improve sensitivity and visibility.

Bandpass Filtering (Butterworth 4th order)
- Default: 5–200 Hz
- Optional tighter filter: 8–150 Hz

Toggle:
USE_TIGHTER_BANDPASS = True/False

3. Threshold & Hysteresis Logic

Primary threshold:
ALARM_THRESHOLD = 0.0999  # mm/s

Bidirectional triggering:
(value >= ALARM_THRESHOLD) or (value <= -ALARM_THRESHOLD)

Optional hysteresis:
USE_HYSTERESIS = True/False
HYSTERESIS_RESET = 0.05  # mm/s

4. Cooldown Logic

After an alarm event completes, the system enters a cooldown phase:
COOLDOWN = 5.2  # seconds

During cooldown, no new events are triggered.

5. 8-Second Event Capture Mode

When the threshold is crossed, the system:
1. Starts event capture immediately
2. Collects all filtered values for exactly 8 seconds
3. Ends capture when 8 seconds pass or the signal falls below the hysteresis reset threshold
4. Computes:
   - Peak value
   - RMS value
   - Event duration
5. Emits a structured alert
6. Enters cooldown

Example alert:

Max value: 0.4123 mm/s
RMS value: 0.1884 mm/s
Duration: 7.82 seconds

6. Anti-Ringing Options

Option A — Tighter Bandpass (8–150 Hz):
USE_TIGHTER_BANDPASS = True

Option B — Hysteresis:
USE_HYSTERESIS = True

Hardware Option:
A 1–2 kΩ shunt resistor across the coil increases damping but reduces sensitivity.

7. Systemd Integration

Script:
/usr/local/bin/geophone_monitor.py

Service:
/etc/systemd/system/geophone-monitor.service

Commands:
sudo systemctl start geophone-monitor
sudo systemctl enable geophone-monitor
sudo systemctl status geophone-monitor
sudo journalctl -u geophone-monitor -f

8. Feature Summary

- ADS1115 geophone acquisition
- SM-6/V2 calibration (mm/s)
- Bandpass filter 5–200 Hz
- Optional tighter bandpass 8–150 Hz
- Bidirectional threshold detection
- Optional hysteresis
- 8-second event capture
- Peak value computation
- RMS computation
- Event duration measurement
- Cooldown (5.2 s)
- systemd background service
- Anti-ringing options

9. Summary

This system provides a robust, DIN-4150-oriented vibration monitoring solution with accurate geophone calibration, real-time filtering, intelligent event detection, detailed event analytics, protection against false triggers, and reliable background operation. It behaves like a compact, professional mini-seismograph suitable for structural monitoring, environmental vibration logging, and machine diagnostics.

10. InfluxDB Integration

The system now includes integration with InfluxDB, a time-series database, to log vibration events and measurements. This allows for efficient storage, querying, and visualization of vibration data over time, enabling long-term monitoring and analysis through compatible dashboards and tools.
