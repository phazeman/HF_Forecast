# HF Propagation Forecast Generator

A Python-based desktop application that generates highly visual, interactive HTML propagation reports. By combining real-time solar data from NOAA with a custom propagation engine, it provides hams with a localized view of band conditions across multiple modes.

## 🚀 Features

* **Live Solar Data**: Automatically fetches SFI, Sunspot Number, and K-Index from NOAA SWPC.
* **Localized Calculations**: Uses your Maidenhead Gridsquare to calculate sun elevation and Grayline paths specific to your QTH.
* **Mode-Specific Analysis**: Separate tabs for **SSB, CW, WSPR, FT8, FT4, and RTTY** with adjusted Signal-to-Noise (SNR) offsets.
* **Station Customization**: Factors in TX power, antenna type (Yagi, Hexbeam, etc.), and local noise floor (Urban/Suburban/Rural).
* **Interactive HTML Reports**: 
    * Dark-themed, high-contrast UI.
    * **Regional Filtering**: Toggle visibility for specific target paths (Europe, North America, etc.).
    * **Grayline Highlighting**: Rows are visually flagged during dawn/dusk transitions.

## 🛠 How It Works

The script operates in three distinct phases:

1.  **Data Retrieval**: Queries NOAA’s JSON feeds for the F10.7 index (SFI) and Planetary K-Index.
2.  **Propagation Engine**: 
    * **MUF**: Calculates Maximum Usable Frequency based on solar flux and sun angle.
    * **Path Logic**: Shifts target regions based on UTC time to simulate Earth's rotation.
    * **Mode Gain**: Digital modes like **WSPR (+42dB)** and **FT8 (+28dB)** receive a reliability boost over **SSB (0dB)**.
3.  **Report Generation**: Data is passed into a Jinja2 template to produce a standalone HTML file with embedded CSS and JS for offline use.

## ⚙️ Configuration (`config.ini`)

The `config.ini` file stores your station defaults. It is created automatically on the first run.

| Section | Key | Possible Values | Description |
| :--- | :--- | :--- | :--- |
| **STATION** | `origin_grid` | String (e.g., `KM72KH`) | Your 6-character Maidenhead locator. |
| | `power` | Integer (1–1500) | Your transmitter output power in Watts. |
| | `tx_antenna` | `Yagi`, `Hexbeam`, `Dipole`, `Vertical`, `Wire` | Transmit antenna type. |
| | `location_type`| `Rural`, `Suburban`, `Urban` | Affects the simulated noise floor. |
| **PREFERENCES**| `active_bands` | Comma-separated list | Default bands checked (e.g., `20m, 40m`). |
| | `active_modes` | Comma-separated list | Default modes checked (e.g., `FT8, SSB`). |

## 📦 Installation & Usage

1.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the App**:
    ```bash
    python hf_forecast.py
    ```
3.  **Generate**: Set your UTC time range, select a save location, and hit **Generate Report**.

## 📝 License
This project is open-source for the amateur radio community. 73!
