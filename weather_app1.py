import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob
import time
import random

# 1. Configuration - Richmond
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT, "longitude": LON,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
    }
    
    # Randomize User-Agent slightly to avoid fingerprinting
    headers = {'User-Agent': f'RichmondBot_{random.randint(1, 1000)}'}
    
    # Try 3 times with a delay between attempts
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # This check prevents the "line 1 column 1" crash
                if not response.text.strip():
                    print(f"Attempt {attempt+1}: Received empty response. Retrying...")
                    time.sleep(10)
                    continue
                return pd.DataFrame(response.json()['hourly'])
            else:
                print(f"Attempt {attempt+1}: Server error {response.status_code}")
                time.sleep(10)
                
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(10)
            
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("Skipping plot: No data received from API after retries.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Plot Lines
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    plt.title(f"Richmond 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated.")

if __name__ == "__main__":
    # Clean up old files
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
    
    # Execute
    weather_data = get_weather_data()
    generate_plot(weather_data)
