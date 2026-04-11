import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import glob

# Richmond/Nelson, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    """Tries Met.no first, then falls back to Open-Meteo if blocked."""
    
    # 1. MET.NO (Yr.no) Attempt
    url_met = "https://met.no"
    # MUST be unique to your project
    headers_met = {'User-Agent': 'RichmondWeatherAppProject/1.1 ://github.com'}
    params_met = {'lat': round(LAT, 4), 'lon': round(LON, 4)}

    try:
        print("Connecting to Met.no...")
        resp = requests.get(url_met, params=params_met, headers=headers_met, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            rows = []
            for entry in data['properties']['timeseries'][:120]:
                rows.append({
                    'time': entry['time'],
                    'temp': entry['data']['instant']['details']['air_temperature'],
                    'wind': entry['data']['instant']['details']['wind_speed'] * 3.6,
                    'rain': entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0)
                })
            return pd.DataFrame(rows)
    except Exception as e:
        print(f"Met.no failed: {e}")

    # 2. OPEN-METEO Fallback (Fixed API URL)
    url_om = "https://open-meteo.com"
    params_om = {
        "latitude": LAT, "longitude": LON,
        "hourly": "precipitation,temperature_2m,wind_speed_10m",
        "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
    }
    
    try:
        print("Falling back to Open-Meteo...")
        resp = requests.get(url_om, params=params_om, timeout=15)
        if resp.status_code == 200:
            d = resp.json()['hourly']
            return pd.DataFrame({
                'time': d['time'], 'temp': d['temperature_2m'],
                'wind': d['wind_speed_10m'], 'rain': d['precipitation']
            })
    except Exception as e:
        print(f"Open-Meteo fallback also failed: {e}")

    return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: All data sources failed.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Left Axis: Temp & Wind
    ax1.plot(df['time'], df['temp'], color='#ff9900', linewidth=3, label='Temp (°C)')
    ax1.plot(df['time'], df['wind'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')
    ax1.set_ylabel('Temp (°C) & Wind (km/h)', fontsize=12)
    ax1.grid(True, alpha=0.1)

    # Right Axis: Rain (Locked at 20mm)
    ax2.plot(df['time'], df['rain'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.set_ylabel('Rainfall (mm)', color='#44aaff', fontsize=12)
    ax2.set_ylim(0, 20)
    ax2.fill_between(df['time'], df['rain'], color='#44aaff', alpha=0.15)

    # Formatting: Days (Mon, Tue) only
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %b'))
    
    plt.title(f"Richmond/Nelson Forecast\nUpdated: {datetime.now().strftime('%a %H:%M')}", fontsize=16)
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success! Created 'weather_latest.png'.")

if __name__ == "__main__":
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    data = get_weather_data()
    generate_plot(data)

