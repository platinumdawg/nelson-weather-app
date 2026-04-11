import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration: Add your specific Nelson-area coordinates
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

def get_weather_data():
    all_lats = ",".join([str(l["lat"]) for l in LOCATIONS])
    all_lons = ",".join([str(l["lon"]) for l in LOCATIONS])
    
    url = "https://open-meteo.com"
    params = {
        "latitude": all_lats,
        "longitude": all_lons,
        "hourly": "precipitation,wind_speed_10m",
        "wind_speed_unit": "kmh",
        "timezone": "Pacific/Auckland",
        "forecast_days": 5  # CHANGED: Now pulling 5 days of data
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Averaging the data from multiple locations
    if isinstance(data, list):
        df_list = [pd.DataFrame(loc['hourly']) for loc in data]
        df = pd.concat(df_list).groupby('time').mean().reset_index()
    else:
        df = pd.DataFrame(data['hourly'])
    
    df['time'] = pd.to_datetime(df['time'])
    return df

def generate_plot(df):
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # X-Axis labels: Format as Day and Hour (e.g., "Mon 12:00")
    # We show a label every 12 hours so the bottom isn't cluttered
    times = df['time'].dt.strftime('%a %H:00')
    
    # NEW: Rain as a LINE
    ax1.plot(times, df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm)')
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontsize=12, fontweight='bold')
    ax1.fill_between(times, df['precipitation'], color='#44aaff', alpha=0.1) # Soft glow under rain
    
    # Wind Speed (Line)
    ax2 = ax1.twinx()
    ax2.plot(times, df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind Speed (km/h)')
    ax2.set_ylabel('Wind Speed (km/h)', color='#00ff00', fontsize=12, fontweight='bold')

    # Formatting the Grid and Labels
    plt.title(f"Nelson 5-Day Forecast \nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fontsize=14)
    plt.xticks(range(0, len(times), 12), times[::12], rotation=45) 
    
    # Summary Box: 5-Day Totals
    total_rain = df['precipitation'].sum()
    max_wind = df['wind_speed_10m'].max()
    summary = f"5-DAY TOTALS: Est. Rain: {total_rain:.1f}mm | Max Peak Wind: {max_wind:.1f}km/h"
    plt.figtext(0.5, 0.02, summary, ha="center", fontsize=11, bbox={"facecolor":"red", "alpha":0.3, "pad":8})
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig('weather_update.png')

if __name__ == "__main__":
    data = get_weather_data()
    generate_plot(data) # Plots all 5 days
