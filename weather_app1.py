import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob

# 1. Setup from Environment and Location
API_KEY = os.getenv('WEATHER_API_KEY')
LAT, LON = -41.3384, 173.1843 # Richmond, NZ

def get_weather_data():
    if not API_KEY:
        print("CRITICAL ERROR: WEATHER_API_KEY secret is missing!")
        return None
        
    # WeatherAPI 5-day forecast (includes hourly data)
    url = f"http://weatherapi.com{API_KEY}&q={LAT},{LON}&days=5&aqi=no&alerts=no"
    
    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200:
            data = response.json()
            hourly_list = []
            
            # Extract hourly data from the nested JSON response
            for day in data['forecast']['forecastday']:
                for hour in day['hour']:
                    hourly_list.append({
                        'time': hour['time'],
                        'temp_c': hour['temp_c'],
                        'wind_kph': hour['wind_kph'],
                        'precip_mm': hour['precip_mm']
                    })
            return pd.DataFrame(hourly_list)
        else:
            print(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("No data available to plot.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Plot Lines
    ax1.plot(df['time'], df['precip_mm'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_kph'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temp_c'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    plt.title(f"Richmond 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    
    # Combined Legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated.")

if __name__ == "__main__":
    # Clean up old weather images
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    # Run process
    data = get_weather_data()
    generate_plot(data)
