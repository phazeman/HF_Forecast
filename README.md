# HF Propagation Forecast Generator (v45)

A professional Python-based desktop application for amateur radio operators. It generates interactive, high-contrast HTML propagation reports by combining real-time solar weather from NOAA with a localized ionospheric engine.

## 🚀 Key Features

* **Live NOAA Integration**: Fetches real-time SFI, Sunspot Number, and K-Index directly from the Space Weather Prediction Center.
* **Localized Path Analysis**: Calculates Sun Elevation and Grayline status based on your specific Maidenhead Gridsquare.
* **Mode-Specific Reliability**: Tabbed HTML reports for **SSB, CW, WSPR, FT8, FT4, and RTTY**.
* **Station Modeling**: Simulates signal performance based on your power, antenna gain, and local noise floor.
* **Interactive Filtering**: Toggle regional paths (e.g., Europe, North America, Oceania) directly within the generated report.

---

## ⚙️ Services Involved

The application relies on several external data streams and libraries to function:

1. **NOAA SWPC (JSON Data Feeds)**: 
   * **F10.7 Index**: Provides the Solar Flux Index (SFI).
   * **Planetary K-Index**: Provides real-time geomagnetic disturbance levels.
2. **Maidenhead Geometry**: An internal coordinate converter translates your 6-character Gridsquare (e.g., KM72KH) into Latitude and Longitude for astronomical calculations.
3. **Jinja2 Templating**: Used to inject calculated propagation data into a responsive, dark-themed HTML/JavaScript wrapper.
4. **CustomTkinter**: Provides the modern, hardware-accelerated GUI for the desktop interface.

---

## 🛠 How It Works (The Engine)

The reliability percentages in your report are not static guesses; they are the result of a multi-stage calculation:

### 1. Astronomical Calculation
The script calculates the **Sun Elevation** for your exact QTH and the target regions for every hour of the requested period.
* **MUF (Maximum Usable Frequency)**: Derived using $MUF = (\frac{SFI}{4.5}) \times \sqrt{\sin(SunElevation)}$. As SFI rises or the sun climbs, higher bands (10m/12m) "open."
* **Grayline Detection**: If sun elevation is between -12° and 2°, the "Grayline" logic triggers, boosting reliability for 40m-160m to simulate enhancement along the terminator.



### 2. Path Modeling
The engine rotates through global "Target Paths" (North America, Europe, Oceania, etc.) based on the UTC hour, simulating where your signal is most likely to land during those specific times of day.

### 3. The Link Budget
The final reliability score is adjusted by your hardware configuration:
* **Antenna Gain**: A Yagi (+18dB) will show significantly higher reliability on a marginal band than a Wire antenna (+2dB).
* **Mode SNR**: Digital modes like **FT8** and **WSPR** receive a mathematical "boost" (up to +42dB) to reflect their ability to decode signals far below the audible noise floor.
* **QRM Simulation**: Choosing "Urban" applies a -18dB penalty to represent high man-made noise.

---

## 📊 Technical Reference

### Antenna Gains (dBi)
| Antenna Type | Internal Gain |
| :--- | :--- |
| **Yagi** | +18 dBi |
| **Hexbeam** | +14 dBi |
| **Dipole** | +6 dBi |
| **Vertical** | +5 dBi |
| **Wire** | +2 dBi |

### Mode Sensitivity Offsets (dB)
| Mode | Sensitivity Boost |
| :--- | :--- |
| **WSPR** | +42 dB |
| **FT8** | +28 dB |
| **FT4** | +22 dB |
| **CW** | +15 dB |
| **RTTY** | +8 dB |
| **SSB** | 0 dB (Baseline) |

---

## 📦 Installation

1. **Install Dependencies**:
   ```bash
   pip install customtkinter requests jinja2 tkcalendar

## Run the Script:

    python hf_forecast.py


73!
Author: Michael (Mike) Spivak (4X5IC)
