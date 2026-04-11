import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration: Add as many Nelson-area coordinates as you like
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

def get_weather_data():
    all_lats = ",".join([str(l["lat"]) for l in LOCATIONS])
    all_lons = ",".join([str(l["lon"]) for l in LOCATIONS])
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": all_lats,
        "longitude": all_lons,
        "hourly": "precipitation,wind_speed_10m,is_day",
        "wind_speed_unit": "kmh",
        "timezone": "Pacific/Auckland",
        "forecast_days": 2
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # If multiple locations, Open-Meteo returns a list. We'll average them for the "Storm Tracker".
    if isinstance(data, list):
        df_list = [pd.DataFrame(loc['hourly']) for loc in data]
        df = pd.concat(df_list).groupby('time').mean().reset_index()
    else:
        df = pd.DataFrame(data['hourly'])
    
    df['time'] = pd.to_datetime(df['time'])
    return df

def generate_plot(df):
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # X-Axis: Hourly 
    times = df['time'].dt.strftime('%H:00')
    
    # Hourly Rain (Bars)
    ax1.bar(times, df['precipitation'], color='#44aaff', alpha=0.6, label='Hourly Rain (mm)')
    ax1.set_ylabel('Rain (mm)', color='#44aaff')
    
    # Wind Speed (Line)
    ax2 = ax1.twinx()
    ax2.plot(times, df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind Speed (km/h)')
    ax2.set_ylabel('Wind Speed (km/h)', color='#00ff00')

    # Storm Tracker Logic (e.g., Wind > 40km/h or Rain > 5mm/hr)
    storms = df[(df['wind_speed_10m'] > 40) | (df['precipitation'] > 5)]
    for storm_time in storms['time']:
        ax1.axvline(storm_time.strftime('%H:00'), color='red', alpha=0.2, linestyle='--')

    # Daily Totals Calculation
    total_rain = df['precipitation'].sum()
    max_wind = df['wind_speed_10m'].max()
    
    plt.title(f"Nelson Hourly Weather & Storm Tracker\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    plt.xticks(times[::3], rotation=45) # Show every 3rd hour for clarity
    
    summary = f"24HR TOTALS: Rain: {total_rain:.1f}mm | Peak Wind: {max_wind:.1f}km/h"
    plt.figtext(0.5, 0.01, summary, ha="center", fontsize=10, bbox={"facecolor":"red", "alpha":0.2, "pad":5})
    
    plt.tight_layout()
    plt.savefig('weather_update.png')

if __name__ == "__main__":
    data = get_weather_data()
    generate_plot(data.head(24)) # Focus on the next 24 hours
