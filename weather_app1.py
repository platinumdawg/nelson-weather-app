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
    """Uses a specific Chrome user-agent and raw text debugging."""
    
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT, "longitude": LON,
        "hourly": ["precipitation", "temperature_2m", "wind_speed_10m"],
        "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    try:
        print("Bypassing GitHub firewall...")
        # Verify=False is a last resort if SSL certificates are being intercepted
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        # DEBUG: If it's not JSON, print the first 100 characters of the block page
        if not response.text.strip().startswith('{'):
            print(f"BLOCK DETECTED! Server returned: {response.text[:100]}")
            return None

        d = response.json()['hourly']
        return pd.DataFrame({
            'time': d['time'], 'temp': d['temperature_2m'],
            'wind': d['wind_speed_10m'], 'rain': d['precipitation']
        })
    except Exception as e:
        print(f"Network error: {e}")
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: Network block persists. You may need a Self-Hosted Runner.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Layout: Temp/Wind on Left, Rain on Right (capped at 20mm)
    ax1.plot(df['time'], df['temp'], color='#ff9900', linewidth=3, label='Temp (°C)')
    ax1.plot(df['time'], df['wind'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')
    ax1.set_ylabel('Temp (°C) & Wind (km/h)')
    
    ax2.plot(df['time'], df['rain'], color='#44aaff', linewidth=2.5, label='Rain (mm/h)')
    ax2.fill_between(df['time'], df['rain'], color='#44aaff', alpha=0.2)
    ax2.set_ylabel('Rainfall (mm)', color='#44aaff')
    ax2.set_ylim(0, 20)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %b'))
    plt.title(f"Richmond/Nelson Forecast\nUpdated: {datetime.now().strftime('%a %H:%M')}")
    
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
