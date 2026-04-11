import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob  # Fixes the NameError

# Richmond, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    # Correct API endpoint for data
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT, "longitude": LON,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
    }
    
    try:
        # Open-Meteo doesn't require a key, but a User-Agent helps identify you
        headers = {'User-Agent': 'NelsonWeatherApp/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            return pd.DataFrame(response.json()['hourly'])
        
        # DEBUG: If GitHub is blocked, this will tell you (e.g., 403 or 429)
        print(f"API rejection! Status: {response.status_code}")
        print(f"Server said: {response.text[:100]}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("Skipping plot: No data received.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Rain on left axis, Wind/Temp on right
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
    # Clean up old files safely
    for f in glob.glob("weather_*.png"):
        if "latest" not in f: 
            try: os.remove(f)
            except: pass
    
    data = get_weather_data()
    generate_plot(data)
