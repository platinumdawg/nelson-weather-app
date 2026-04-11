import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import glob
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 1. Configuration
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

RAIN_MAX, WIND_MAX, TEMP_MAX, TEMP_MIN = 10.0, 20.0, 20.0, 0.0

def cleanup_old_files(days_to_keep=5):
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    for f in glob.glob("weather_*.png"):
        if "latest" in f: continue
        try:
            if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
                os.remove(f)
        except: pass

def get_weather_data():
    all_dfs = []
    url = "https://open-meteo.com"
    
    # Session with Retries and realistic Headers
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    for loc in LOCATIONS:
        params = {
            "latitude": loc["lat"], "longitude": loc["lon"],
            "hourly": "precipitation,wind_speed_10m,temperature_2m",
            "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
        }
        try:
            res = session.get(url, params=params, headers=headers, timeout=20)
            print(f"Checking {loc['name']}: Status {res.status_code}")
            
            # Check content-type to ensure it is actually JSON
            if "application/json" in res.headers.get("Content-Type", ""):
                data = res.json()
                df = pd.DataFrame(data['hourly'])
                df['time'] = pd.to_datetime(df['time'])
                all_dfs.append(df)
            else:
                print(f"Warning: Received non-JSON response for {loc['name']}: {res.text[:50]}")
        except Exception as e:
            print(f"Request failed for {loc['name']}: {e}")

    return pd.concat(all_dfs).groupby('time').mean().reset_index() if all_dfs else None

def generate_plot(df):
    if df is None:
        print("CRITICAL: No data to plot.")
        return

    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    def format_time(t):
        if t.hour == 12: return f"{t.strftime('%a')}\nDay"
        if t.hour == 0: return f"{t.strftime('%a')}\nNight"
        return ""
    
    time_labels = [format_time(t) for t in df['time']]
    tick_indices = [i for i, label in enumerate(time_labels) if label != ""]

    # Plots
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    # Alerts
    if df['precipitation'].max() >= RAIN_MAX:
        ax1.axhline(y=RAIN_MAX, color='cyan', linestyle='--', alpha=0.5, label='RAIN ALERT')
    if df['wind_speed_10m'].max() >= WIND_MAX:
        ax2.axhline(y=WIND_MAX, color='lime', linestyle='--', alpha=0.5, label='WIND ALERT')
    if df['temperature_2m'].max() >= TEMP_MAX:
        ax2.axhline(y=TEMP_MAX, color='red', linestyle=':', alpha=0.7, label='HEAT ALERT')
    if df['temperature_2m'].min() <= TEMP_MIN:
        ax2.axhline(y=TEMP_MIN, color='white', linestyle=':', alpha=0.7, label='FROST ALERT')

    plt.title(f"Nelson Smart Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}", fontsize=14)
    ax1.set_xticks(df['time'][tick_indices])
    ax1.set_xticklabels([time_labels[i] for i in tick_indices])
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontweight='bold')
    ax2.set_ylabel('Wind / Temp', color='#ff9900', fontweight='bold')

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', frameon=True, facecolor='black')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    plt.tight_layout()
    plt.savefig(f"weather_{timestamp}.png")
    plt.savefig("weather_latest.png")
    print(f"Success: Files created at {timestamp}")

if __name__ == "__main__":
    cleanup_old_files()
    forecast_data = get_weather_data()
    generate_plot(forecast_data)
