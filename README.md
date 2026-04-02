# HF Propagation Forecast Generator

A professional Python-based desktop application for amateur radio operators. It generates interactive, high-contrast HTML propagation reports by combining real-time solar weather from NOAA with a localized ionospheric engine.

## 🚀 Key Features

* **Live NOAA Integration**: Fetches real-time SFI, SN, and K-Index from the SWPC.
* **Localized Path Analysis**: Calculates Sun Elevation and Grayline status based on your Maidenhead Gridsquare.
* **Mode-Specific Reliability**: Separate analysis for **SSB, CW, WSPR, FT8, FT4, and RTTY**.
* **Automation Mode**: Run headless reports via Command Line for scheduled tasks.
* **Adaptive UI**: High-contrast interface compatible with both **Light** and **Dark** desktop themes.

---

## 🤖 Automation & CLI Usage

You can run the script directly from the Command Prompt (CMD) or terminal without opening the GUI. This mode uses your `config.ini` settings and automatically generates a 24-hour forecast starting from the current UTC time.

### Basic Auto-Run
Generates a report using default naming: `Propagation_[GRID]_[DATE]_AUTO.html`
---
bash
  python hf_forecast.py auto
---


### Custom File Output
Direct the report to a specific folder or filename using the file= parameter:
```
  python hf_forecast.py auto file="C:\Reports\Daily_HF_Report.html"
```
Note: Use double quotes if your file path contains spaces.
---


## ⚙️ Services Involved

The application relies on several external data streams and libraries to function:

1. **NOAA SWPC (JSON Data Feeds)**: 
   * **F10.7 Index**: Provides the Solar Flux Index (SFI) used for MUF calculations.
   * **Planetary K-Index**: Provides real-time geomagnetic disturbance levels to calculate signal degradation.
2. **Maidenhead Geometry**: An internal coordinate converter translates your 6-character Gridsquare (e.g., KM72KH) into Latitude and Longitude for precise astronomical calculations.
3. **Jinja2 Templating**: Used to inject calculated propagation data into a responsive, dark-themed HTML/JavaScript wrapper.
4. **CustomTkinter**: Provides the modern, hardware-accelerated GUI for the desktop interface.

---

## 🛠 How It Works (The Engine)

The reliability percentages in your report are calculated using a multi-stage propagation model:

### 1. Astronomical Calculation
The script calculates the **Sun Elevation** for your exact QTH and target regions for every hour of the requested period.
* **MUF (Maximum Usable Frequency)**: Derived using $MUF = (\frac{SFI}{4.5}) \times \sqrt{\sin(SunElevation)}$. As SFI rises or the sun climbs, higher bands (10m/12m) "open."
* **Grayline Detection**: If sun elevation is between -12° and 2°, the "Grayline" logic triggers, boosting reliability for 40m-160m to simulate enhancement along the terminator.

### 2. Path Modeling
The engine rotates through global "Target Paths" (North America, Europe, Oceania, etc.) based on the UTC hour, simulating where your signal is most likely to land during those specific times of day.

### 3. The Link Budget
The final reliability score is adjusted by your hardware configuration:
* **Antenna Gain**: A Yagi (+18dB) will show significantly higher reliability on a marginal band than a Wire antenna (+2dB).
* **Mode SNR**: Digital modes like **FT8** and **WSPR** receive a mathematical "boost" (up to +42dB) to reflect their ability to decode signals far below the audible noise floor.
* **QRM Simulation**: Choosing "Urban" applies a -18dB penalty to represent high man-made noise levels.

---

## ⚙️ Configuration (`config.ini`)

The application uses a `config.ini` file for persistent settings. The script reads these values at startup to populate the GUI.

### [STATION] Section
* **`origin_grid`**: Your 4 or 6-character Maidenhead locator (e.g., `KM72KH`).
* **`power`**: Your transmitter output in Watts. Recommended range: `1` to `1500`.
* **`tx_antenna` / `rx_antenna`**: Defines gain offsets. 
  * *Values:* `Yagi`, `Hexbeam`, `Dipole`, `Vertical`, `Wire`
* **`location_type`**: Sets the local noise floor. 
  * *Values:* `Rural` (best), `Suburban`, `Urban` (worst)

### [PREFERENCES] Section
* **`theme`**: Sets the visual look of the GUI. 
  * *Values:* `Dark`, `Light`, `System`
* **`active_bands`**: A comma-separated list of bands checked by default.
  * *Values:* `160m`, `80m`, `40m`, `30m`, `20m`, `17m`, `15m`, `12m`, `10m`, `6m`
* **`active_modes`**: A comma-separated list of modes checked by default.
  * *Values:* `SSB`, `CW`, `WSPR`, `FT8`, `FT4`, `RTTY`

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

**73!**

**Author:** Michael (Mike) Spivak (4X5IC)
