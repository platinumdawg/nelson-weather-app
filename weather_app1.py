import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

RAIN_THRESHOLD = 10  # mm per hour
WIND_THRESHOLD = 20  # km per hour

def get_weather_data():
    all_dfs = []
    url = "https://api.open-meteo.com/v1/forecast"
    
    for loc in LOCATIONS:
        params = {
            "latitude": loc["lat"],
            "longitude": loc["lon"],
            "hourly": "precipitation,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "Pacific/Auckland",
            "forecast_days": 5
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data['hourly'])
                df['time'] = pd.to_datetime(df['time'])
                all_dfs.append(df)
            else:
                print(f"Skipping {loc['name']}: API returned status {response.status_code}")
        except Exception as e:
            print(f"Error fetching data for {loc['name']}: {e}")

    if not all_dfs:
        return None
        
    # Average the data across all successfully fetched locations
    combined_df = pd.concat(all_dfs).groupby('time').mean().reset_index()
    return combined_df

def generate_plot(df):
    if df is None: return
    
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    times = df['time'].dt.strftime('%a %H:00')

    # --- RAIN LINE & WARNINGS ---
    ax1.plot(times, df['precipitation'], color='#44aaff', linewidth=2.5, label='Rain (mm/h)')
    ax1.axhline(y=RAIN_THRESHOLD, color='cyan', linestyle='--', alpha=0.5, label='Heavy Rain Warning (10mm)')
    # Highlight high rain areas
    ax1.fill_between(times, df['precipitation'], RAIN_THRESHOLD, where=(df['precipitation'] >= RAIN_THRESHOLD), 
                     color='cyan', alpha=0.3, interpolate=True)
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontsize=12, fontweight='bold')

    # --- WIND LINE & WARNINGS ---
    ax2 = ax1.twinx()
    ax2.plot(times, df['wind_speed_10m'], color='#00ff00', linewidth=2.5, label='Wind Speed (km/h)')
    ax2.axhline(y=WIND_THRESHOLD, color='yellow', linestyle='--', alpha=0.5, label='High Wind Warning (20km/h)')
    # Highlight high wind areas
    ax2.fill_between(times, df['wind_speed_10m'], WIND_THRESHOLD, where=(df['wind_speed_10m'] >= WIND_THRESHOLD), 
                     color='yellow', alpha=0.2, interpolate=True)
    ax2.set_ylabel('Wind Speed (km/h)', color='#00ff00', fontsize=12, fontweight='bold')

    # --- FORMATTING ---
    plt.title(f"Nelson 5-Day Multi-Location Forecast\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fontsize=14)
    plt.xticks(range(0, len(times), 12), times[::12], rotation=45) 
    
    # Combined Legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='black')

    # Summary Text
    total_rain = df['precipitation'].sum()
    max_wind = df['wind_speed_10m'].max()
    summary = f"5-DAY OUTLOOK: Total Est. Rain: {total_rain:.1f}mm | Peak Wind: {max_wind:.1f}km/h"
    plt.figtext(0.5, 0.02, summary, ha="center", fontsize=12, bbox={"facecolor":"red", "alpha":0.4, "pad":10})

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig('weather_update.png')

if __name__ == "__main__":
    forecast_df = get_weather_data()
    generate_plot(forecast_df)
