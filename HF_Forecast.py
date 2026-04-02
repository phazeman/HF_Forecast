import os
import configparser
import requests
import math
from datetime import datetime, timedelta, timezone
from jinja2 import Template
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry

# --- CONFIGURATION ---
CONFIG_FILE = "config.ini"

def load_config():
    config = configparser.ConfigParser(allow_no_value=True)
    if not os.path.exists(CONFIG_FILE):
        config.add_section('STATION')
        config.set('STATION', 'origin_grid', 'KM72KH')
        config.set('STATION', 'power', '100')
        config.set('STATION', 'tx_antenna', 'Yagi')
        config.set('STATION', 'rx_antenna', 'Yagi')
        config.set('STATION', 'location_type', 'Suburban')
        config.add_section('PREFERENCES')
        config.set('PREFERENCES', 'active_bands', '10m, 12m, 15m, 17m, 20m, 40m')
        config.set('PREFERENCES', 'active_modes', 'SSB, FT8')
        config.set('PREFERENCES', 'theme', 'Dark')
        with open(CONFIG_FILE, 'w') as f: config.write(f)
    else:
        config.read(CONFIG_FILE)
    return config

conf = load_config()

# --- ENGINE LOGIC ---
def get_sun_elevation(lat, lon, dt_utc):
    day = dt_utc.timetuple().tm_yday
    decl = 23.45 * math.sin(math.radians(360 / 365 * (day - 81)))
    time_offset = lon / 15.0
    solar_time = (dt_utc.hour + dt_utc.minute/60.0 + time_offset) % 24
    hour_angle = (solar_time - 12) * 15
    lat_rad, decl_rad, ha_rad = map(math.radians, [lat, decl, hour_angle])
    sin_el = (math.sin(lat_rad) * math.sin(decl_rad) + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(ha_rad))
    return math.degrees(math.asin(sin_el))

def fetch_solar_data():
    try:
        sfi_json = requests.get("https://services.swpc.noaa.gov/json/solar-cycle/f107_index.json", timeout=5).json()[-1]
        sfi = float(sfi_json['f107'])
        sn = int((sfi - 60) * 1.1)
        kp_json = requests.get("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", timeout=5).json()[-1]
        kp = float(kp_json['kp_index'])
        a_idx = int(kp * 7)
        return sfi, kp, a_idx, sn
    except: return 145.0, 1.0, 6, 130

def grid_to_latlon(grid):
    grid = grid.upper()
    try:
        lon = (ord(grid[0]) - ord('A')) * 20 - 180 + (int(grid[2]) * 2)
        lat = (ord(grid[1]) - ord('A')) * 10 - 90 + int(grid[3])
        return lat, lon
    except: return 0, 0

def calculate_forecast(lat, lon, start_utc, end_utc, bands, modes, power, tx_ant, rx_ant, loc_type):
    sfi, kp, a_idx, sn = fetch_solar_data()
    results = []
    current_dt = start_utc
    mode_offsets = {"WSPR": 42, "FT8": 28, "FT4": 22, "CW": 15, "RTTY": 8, "SSB": 0}
    ant_gains = {"Yagi": 18, "Hexbeam": 14, "Dipole": 6, "Vertical": 5, "Wire": 2}
    noise_pen = {"Rural": 10, "Suburban": -5, "Urban": -18}
    band_freqs = {"6m": 50, "10m": 28, "12m": 24, "15m": 21, "17m": 18, "20m": 14, "30m": 10, "40m": 7, "80m": 3.5, "160m": 1.8}
    station_boost = (10 * math.log10(max(1, int(power)) / 100)) + ant_gains.get(tx_ant, 0) + ant_gains.get(rx_ant, 0) + noise_pen.get(loc_type, 0)

    while current_dt <= end_utc:
        sun_el = get_sun_elevation(lat, lon, current_dt)
        if 8 <= current_dt.hour <= 14: path, target_lat, target_lon = "Europe", 50, 10
        elif 14 < current_dt.hour <= 20: path, target_lat, target_lon = "North America", 40, -90
        elif 20 < current_dt.hour <= 24 or 0 <= current_dt.hour < 4: path, target_lat, target_lon = "Americas / Oceania", -20, -60
        else: path, target_lat, target_lon = "Asia / Africa", 10, 80
        mid_lat, mid_lon = (lat + target_lat) / 2, (lon + target_lon) / 2
        mid_sun = get_sun_elevation(mid_lat, mid_lon, current_dt)
        is_gl = -12 <= sun_el <= 2
        row = {"timestamp": current_dt.strftime("%d/%m %H:00 UTC"), "sun_el": f"{sun_el:.1f}°", "is_gl": is_gl, "sfi": sfi, "kp": kp, "a_idx": a_idx, "sn": sn, "best_path": path}
        muf = (sfi / 4.5) * math.sqrt(max(0.1, math.sin(math.radians(max(0, mid_sun + 10)))))
        for band in bands:
            f = band_freqs.get(band, 14)
            if f > muf * 1.15: base = 5
            elif f > muf: base = 25
            else: base = 50 + (35 * (f / muf)) 
            if mid_sun > 0 and f < 10: base -= (mid_sun * 0.8)
            kp_hit = kp * (8 if f < 15 else 3)
            for mode in modes:
                rel = base + station_boost + mode_offsets.get(mode, 0) - kp_hit
                if is_gl and f < 12: rel += 20
                val = max(5, min(99, int(rel)))
                row[f"{band}_{mode}"] = val
                row[f"{band}_{mode}_clr"] = "#28a745" if val >= 70 else "#ffc107" if val >= 35 else "#dc3545"
        results.append(row); current_dt += timedelta(hours=1)
    return results

def generate_html(grid, data, filepath, bands, modes, power, tx_ant, rx_ant, loc_type):
    regions = sorted(list(set(row['best_path'] for row in data)))
    html_template = """
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>HF_Forecast_{{ grid }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0c0c0c; color: #e0e0e0; padding: 30px; font-size: 19px; }
        .card { background: #1a1a1a; padding: 25px; border-radius: 12px; border: 1px solid #333; }
        h1 { font-size: 33px; margin-bottom: 20px; text-align: center; }
        .solar-status { display: flex; gap: 40px; margin-bottom: 20px; padding: 15px; background: #252525; border-radius: 8px; border-left: 5px solid #00e5ff; align-items: center; justify-content: center; }
        .solar-item { font-size: 19px; color: #aaa; text-align: center; }
        .solar-val { color: #ffb300; font-weight: bold; font-size: 21px; display: block; }
        .filter-section { text-align: center; margin-bottom: 25px; padding: 15px; background: #222; border-radius: 8px; }
        .filter-title { font-weight: bold; color: #00e5ff; margin-right: 15px; font-size: 18px; }
        .filter-label { margin: 0 10px; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; }
        .filter-checkbox { transform: scale(1.3); }
        .tabs { display: flex; gap: 5px; border-bottom: 2px solid #444; margin-top: 20px; }
        .tab-btn { background: #2a2a2a; color: #888; border: none; padding: 15px 30px; cursor: pointer; border-radius: 8px 8px 0 0; font-weight: bold; font-size: 19px; }
        .tab-btn.active { background: #00e5ff; color: #000; }
        .tab-content { display: none; padding-top: 20px; overflow-x: auto; }
        .tab-content.active { display: block; }
        table { width: 100%; border-collapse: collapse; text-align: center; font-size: 19px; }
        th { background: #222; color: #00e5ff; padding: 15px; border-bottom: 2px solid #444; font-size: 20px; }
        td { padding: 12px; border-bottom: 1px solid #282828; }
        .gl-row { background: #2d243a !important; }
        .rel { font-weight: bold; padding: 6px 12px; border-radius: 4px; color: white; display: inline-block; min-width: 50px; }
        .gl-tag { background: #00e5ff; color: #000; font-size: 14px; padding: 3px 8px; border-radius: 3px; margin-left: 8px; font-weight: bold; }
        .path-col { color: #00e5ff; font-weight: 500; font-size: 17px; }
    </style></head><body><div class="card">
    <h1>HF Propagation Path Analysis: {{ grid }}</h1>
    <div class="solar-status">
        <div class="solar-item">SFI<span class="solar-val">{{ data[0].sfi }}</span></div>
        <div class="solar-item">SN<span class="solar-val">{{ data[0].sn }}</span></div>
        <div class="solar-item">A-IDX<span class="solar-val">{{ data[0].a_idx }}</span></div>
        <div class="solar-item">K-IDX<span class="solar-val">{{ data[0].kp }}</span></div>
        <div style="border-left: 1px solid #444; height: 40px; margin: 0 20px;"></div>
        <div style="font-size: 16px; color: #777;">{{ power }}W | {{ tx_ant }} | {{ loc_type }}</div>
    </div>
    <div class="filter-section">
        <span class="filter-title">Filter by Region:</span>
        {% for region in regions %}<label class="filter-label"><input type="checkbox" class="filter-checkbox" checked onchange="updateFilters()" data-region="{{ region }}"> {{ region }}</label>{% endfor %}
    </div>
    <div class="tabs">{% for mode in modes %}<button class="tab-btn {% if loop.first %}active{% endif %}" onclick="openTab(event, '{{ mode }}')">{{ mode }}</button>{% endfor %}</div>
    {% for mode in modes %}<div id="{{ mode }}" class="tab-content {% if loop.first %}active{% endif %}">
        <table><thead><tr><th>Time (UTC)</th><th>Sun El.</th>{% for band in bands %}<th>{{ band }}</th>{% endfor %}<th>Target Path</th></tr></thead>
        <tbody>{% for row in data %}<tr class="data-row {% if row.is_gl %}gl-row{% endif %}" data-region="{{ row.best_path }}">
            <td><b>{{ row.timestamp }}</b></td><td>{{ row.sun_el }}{% if row.is_gl %}<span class="gl-tag">GRAYLINE</span>{% endif %}</td>
            {% for band in bands %}{% set key = band + '_' + mode %}<td><span class="rel" style="background:{{ row[key+'_clr'] }}">{{ row[key] }}%</span></td>{% endfor %}
            <td class="path-col">{{ row.best_path }}</td>
        </tr>{% endfor %}</tbody></table></div>{% endfor %}
    </div><script>
    function openTab(e,m){var i,tc,tb;tc=document.getElementsByClassName("tab-content");for(i=0;i<tc.length;i++)tc[i].classList.remove("active");tb=document.getElementsByClassName("tab-btn");for(i=0;i<tb.length;i++)tb[i].classList.remove("active");document.getElementById(m).classList.add("active");e.currentTarget.classList.add("active");}
    function updateFilters() {
        const checks = document.querySelectorAll('.filter-checkbox');
        const activeRegions = Array.from(checks).filter(c => c.checked).map(c => c.getAttribute('data-region'));
        const rows = document.querySelectorAll('.data-row');
        rows.forEach(row => { row.style.display = activeRegions.includes(row.getAttribute('data-region')) ? '' : 'none'; });
    }
    </script></body></html>
    """
    with open(filepath, "w", encoding="utf-8") as f: f.write(Template(html_template).render(grid=grid, data=data, bands=bands, modes=modes, power=power, tx_ant=tx_ant, rx_ant=rx_ant, loc_type=loc_type, regions=regions))

# --- GUI ---
class VoacapGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HF Propagation Forecast Generator")
        
        # Define Adaptive Colors for Theme Consistency
        self.accent_color = ("#008FB3", "#00e5ff")  # Darker for light mode, cyan for dark mode
        self.sub_bg = ("#EBEBEB", "#252525")        # Light gray for light mode, dark gray for dark mode
        self.inner_bg = ("#DEDEDE", "#1e1e1e")      # Darker inner panels

        # Apply theme from config
        ctk.set_appearance_mode(conf.get('PREFERENCES', 'theme', fallback='Dark'))
        
        self.save_path = ""
        now_utc = datetime.now(timezone.utc)
        start_def = now_utc.replace(minute=0, second=0, microsecond=0)
        end_def = start_def + timedelta(days=1)

        # Header
        ctk.CTkLabel(self, text="HF Propagation Forecast Generator", font=("Segoe UI", 26, "bold"), text_color=self.accent_color).pack(pady=(20, 10))
        
        # Station Frame
        f1 = ctk.CTkFrame(self, fg_color="transparent"); f1.pack(pady=5)
        ctk.CTkLabel(f1, text="Gridsquare :").pack(side="left", padx=(0, 5))
        self.grid_e = ctk.CTkEntry(f1, width=110, placeholder_text="KM72KH"); self.grid_e.insert(0, conf.get('STATION', 'origin_grid', fallback='KM72KH')); self.grid_e.pack(side="left", padx=5)
        self.loc_m = ctk.CTkOptionMenu(f1, values=["Rural", "Suburban", "Urban"], width=130); self.loc_m.set(conf.get('STATION', 'location_type', fallback='Suburban')); self.loc_m.pack(side="left", padx=5)
        
        # Hardware Frame
        f2 = ctk.CTkFrame(self, fg_color=self.sub_bg); f2.pack(pady=10, padx=20, fill="x")
        f2_inner = ctk.CTkFrame(f2, fg_color="transparent"); f2_inner.pack(expand=True)
        ctk.CTkLabel(f2_inner, text="Power (W):").grid(row=0, column=0, padx=5, pady=10)
        self.pwr = ctk.CTkEntry(f2_inner, width=60); self.pwr.insert(0, conf.get('STATION', 'power', fallback='100')); self.pwr.grid(row=0, column=1, padx=5)
        ants = ["Wire", "Vertical", "Dipole", "Hexbeam", "Yagi"]
        ctk.CTkLabel(f2_inner, text="TX Ant:").grid(row=0, column=2, padx=5); self.tx_a = ctk.CTkOptionMenu(f2_inner, values=ants, width=110); self.tx_a.set(conf.get('STATION', 'tx_antenna', fallback='Yagi')); self.tx_a.grid(row=0, column=3, padx=5)
        ctk.CTkLabel(f2_inner, text="RX Ant:").grid(row=0, column=4, padx=5); self.rx_a = ctk.CTkOptionMenu(f2_inner, values=ants, width=110); self.rx_a.set(conf.get('STATION', 'rx_antenna', fallback='Yagi')); self.rx_a.grid(row=0, column=5, padx=5)
        
        # Band Selection
        b_frame = ctk.CTkFrame(self, fg_color=self.inner_bg); b_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(b_frame, text="— HF BANDS —", font=("Segoe UI", 13, "bold"), text_color=self.accent_color).pack(pady=(5, 0))
        self.bands = ["6m", "10m", "12m", "15m", "17m", "20m", "30m", "40m", "80m", "160m"]
        active_b = [x.strip() for x in conf.get('PREFERENCES', 'active_bands', fallback='10m, 15m, 20m, 40m').split(',')]
        self.b_vars = {b: ctk.StringVar(value=b if b in active_b else "off") for b in self.bands}
        bi = ctk.CTkFrame(b_frame, fg_color="transparent"); bi.pack(pady=5)
        for i, b in enumerate(self.bands): ctk.CTkCheckBox(bi, text=b, variable=self.b_vars[b], onvalue=b, offvalue="off", width=75).grid(row=i//5, column=i%5, padx=4, pady=2)
        
        # Mode Selection
        m_frame = ctk.CTkFrame(self, fg_color=self.inner_bg); m_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(m_frame, text="— MODES —", font=("Segoe UI", 13, "bold"), text_color=self.accent_color).pack(pady=(5, 0))
        self.modes = ["SSB", "CW", "WSPR", "FT8", "FT4", "RTTY"]
        active_m = [x.strip() for x in conf.get('PREFERENCES', 'active_modes', fallback='SSB, FT8').split(',')]
        self.m_vars = {m: ctk.StringVar(value=m if m in active_m else "off") for m in self.modes}
        mi = ctk.CTkFrame(m_frame, fg_color="transparent"); mi.pack(pady=5)
        for i, m in enumerate(self.modes): ctk.CTkCheckBox(mi, text=m, variable=self.m_vars[m], onvalue=m, offvalue="off", width=90).grid(row=0, column=i, padx=4)
        
        # Date section (UTC)
        ctk.CTkLabel(self, text="- DATE/TIME (UTC) -", font=("Segoe UI", 13, "bold"), text_color=self.accent_color).pack(pady=(10, 0))
        t_frame = ctk.CTkFrame(self, fg_color="transparent"); t_frame.pack(pady=10)
        self.s_cal = DateEntry(t_frame, width=11, date_pattern='d/m/yyyy'); self.s_cal.set_date(start_def)
        self.s_cal.pack(side="left", padx=5)
        self.s_h = ctk.CTkComboBox(t_frame, values=[f"{i:02d}:00" for i in range(24)], width=85); self.s_h.set(start_def.strftime("%H:00")); self.s_h.pack(side="left")
        ctk.CTkLabel(t_frame, text="to").pack(side="left", padx=5)
        self.e_cal = DateEntry(t_frame, width=11, date_pattern='d/m/yyyy'); self.e_cal.set_date(end_def)
        self.e_cal.pack(side="left", padx=5)
        self.e_h = ctk.CTkComboBox(t_frame, values=[f"{i:02d}:00" for i in range(24)], width=85); self.e_h.set(end_def.strftime("%H:00")); self.e_h.pack(side="left")
        
        self.path_btn = ctk.CTkButton(self, text="📁 Set Save Location", command=self.select_path, fg_color=("#555", "#333"), height=35); self.path_btn.pack(pady=(15, 10), padx=40, fill="x")
        self.btn = ctk.CTkButton(self, text="🚀 GENERATE REPORT", command=self.run, fg_color="#28a745", font=("Segoe UI", 15, "bold"), height=50); self.btn.pack(pady=(0, 20), padx=40, fill="x")

    def select_path(self):
        grid = self.grid_e.get().strip().upper() or "STATION"
        date_str = datetime.now(timezone.utc).strftime('%d-%m-%Y')
        self.save_path = filedialog.asksaveasfilename(defaultextension=".html", initialfile=f"Propagation_{grid}_{date_str}.html")
        if self.save_path: self.path_btn.configure(text="Path Ready ✔", fg_color="#1f538d")

    def run(self):
        grid = self.grid_e.get().upper(); pwr = self.pwr.get()
        sel_b = [v.get() for v in self.b_vars.values() if v.get() != "off"]
        sel_b = [b for b in self.bands if b in sel_b]
        sel_m = [v.get() for v in self.m_vars.values() if v.get() != "off"]
        if not (self.save_path and sel_b and sel_m):
            messagebox.showerror("Selection Error", "Check configuration.")
            return
        try:
            start_dt = datetime.combine(self.s_cal.get_date(), datetime.strptime(self.s_h.get(), "%H:%M").time()).replace(tzinfo=timezone.utc)
            end_dt = datetime.combine(self.e_cal.get_date(), datetime.strptime(self.e_h.get(), "%H:%M").time()).replace(tzinfo=timezone.utc)
            lat, lon = grid_to_latlon(grid)
            data = calculate_forecast(lat, lon, start_dt, end_dt, sel_b, sel_m, pwr, self.tx_a.get(), self.rx_a.get(), self.loc_m.get())
            generate_html(grid, data, self.save_path, sel_b, sel_m, pwr, self.tx_a.get(), self.rx_a.get(), self.loc_m.get())
            messagebox.showinfo("Success", "Report Generated")
        except Exception as e: messagebox.showerror("Error", f"Error: {e}")

if __name__ == "__main__": app = VoacapGui(); app.mainloop()