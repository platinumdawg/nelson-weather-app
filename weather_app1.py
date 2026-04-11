import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import glob

# 1. Configuration - Richmond Only
LAT, LON = -41.3384, 173.1843
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
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "wind_speed_unit": "kmh",
        "timezone": "Pacific/Auckland",
        "forecast_days": 5
    }
    try:
        # Standard JSON request avoids the 'unpack' buffer error
        res = requests.get(url, params=params, timeout=20)
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data['hourly'])
            df['time'] = pd.to_datetime(df['time'])
            return df
        else:
            print(f"API Error: {res.status_code}")
    except Exception as e:
        print(f"Connection failed: {e}")
    return None

def generate_plot(df):
    if df is None: return
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    def format_time(t):
        if t.hour == 12: return f"{t.strftime('%a')}\nDay"
        if t.hour == 0: return f"{t.strftime('%a')}\nNight"
        return ""
    
    time_labels = [format_time(t) for t in df['time']]
    tick_indices = [i for i, label in enumerate(time_labels) if label != ""]

    # Main Lines
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    # Smart Alerts
    if df['precipitation'].max() >= RAIN_MAX:
        ax1.axhline(y=RAIN_MAX, color='cyan', linestyle='--', alpha=0.5, label='RAIN ALERT')
    if df['wind_speed_10m'].max() >= WIND_MAX:
        ax2.axhline(y=WIND_MAX, color='lime', linestyle='--', alpha=0.5, label='WIND ALERT')
    if df['temperature_2m'].max() >= TEMP_MAX:
        ax2.axhline(y=TEMP_MAX, color='red', linestyle=':', alpha=0.7, label='HEAT ALERT')
    if df['temperature_2m'].min() <= TEMP_MIN:
        ax2.axhline(y=TEMP_MIN, color='white', linestyle=':', alpha=0.7, label='FROST ALERT')

    plt.title(f"Richmond 5-Day Smart Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    ax1.set_xticks(df['time'][tick_indices])
    ax1.set_xticklabels([time_labels[i] for i in tick_indices])
    ax1.set_ylabel('Rain (mm)', color='#44aaff')
    ax2.set_ylabel('Wind / Temp', color='#ff9900')

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', frameon=True, facecolor='black')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    plt.tight_layout()
    plt.savefig(f"weather_{timestamp}.png")
    plt.savefig("weather_latest.png")
    print(f"Success: Saved weather_{timestamp}.png")

if __name__ == "__main__":
    cleanup_old_files()
    data = get_weather_data()
    generate_plot(data)
