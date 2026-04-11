import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob

# Nelson/Richmond, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    # FIXED: The correct API endpoint for Open-Meteo
    api_url = "https://open-meteo.com"
    
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "precipitation,temperature_2m,wind_speed_10m",
        "wind_speed_unit": "kmh",
        "timezone": "Pacific/Auckland",
        "forecast_days": 5
    }

    try:
        print(f"Fetching Nelson weather from Open-Meteo...")
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            # Convert JSON response to DataFrame
            data = response.json()
            return pd.DataFrame(data['hourly'])
        else:
            print(f"API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: No data to plot.")
        return
        
    # Prepare data
    df['time'] = pd.to_datetime(df['time'])
    
    # Setup Plot
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Plotting
    ax1.bar(df['time'], df['precipitation'], color='#44aaff', alpha=0.5, label='Rain (mm/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')

    # Labels & Styling
    plt.title(f"Richmond/Nelson 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    ax1.set_ylabel('Rainfall (mm)')
    ax2.set_ylabel('Temp (°C) / Wind (km/h)')
    
    # Merge legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated.")

if __name__ == "__main__":
    # Cleanup old local images
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    weather_df = get_weather_data()
    generate_plot(weather_df)
