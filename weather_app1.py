import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import glob

# 1. Configuration - Nelson Locations
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

# 2. Warning Thresholds (Lines only appear if these are hit)
RAIN_MAX = 10.0   # mm per hour
WIND_MAX = 20.0   # km per hour
TEMP_MAX = 20.0   # °C
TEMP_MIN = 0.0    # °C

def cleanup_old_files(days_to_keep=5):
    """Deletes png files older than 5 days to keep the repo clean."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    files = glob.glob("weather_*.png")
    for f in files:
        if "latest" in f:
            continue
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(f))
            if file_time < cutoff:
                os.remove(f)
                print(f"Deleted old file: {f}")
        except Exception as e:
            print(f"Cleanup error: {e}")

def get_weather_data():
    """Fetches data from Open-Meteo API."""
    all_dfs = []
    # Corrected API Endpoint
    url = "https://open-meteo.com"
    
    for loc in LOCATIONS:
        params = {
            "latitude": loc["lat"], 
            "longitude": loc["lon"],
            "hourly": "precipitation,wind_speed_10m,temperature_2m",
            "wind_speed_unit": "kmh", 
            "timezone": "Pacific/Auckland", 
            "forecast_days": 5
        }
        try:
            res = requests.get(url, params=params, timeout=15)
            if res.status_code == 200:
                df = pd.DataFrame(res.json()['hourly'])
                df['time'] = pd.to_datetime(df['time'])
                all_dfs.append(df)
            else:
                print(f"API Error {res.status_code} for {loc['name']}")
        except Exception as e: 
            print(f"Connection Error for {loc['name']}: {e}")

    if not all_dfs:
        print("CRITICAL ERROR: No weather data could be fetched.")
        return None
        
    return pd.concat(all_dfs).groupby('time').mean().reset_index()

def generate_plot(df):
    """Creates the 5-day graph with smart alerts."""
    if df is None:
        return

    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Create Day/Night Labels for X-Axis
    def format_time(t):
        if t.hour == 12: return f"{t.strftime('%a')}\nDay"
        if t.hour == 0: return f"{t.strftime('%a')}\nNight"
        return ""
    
    time_labels = [format_time(t) for t in df['time']]
    tick_indices = [i for i, label in enumerate(time_labels) if label != ""]

    # --- PLOT DATA ---
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    # --- SMART ALERTS (Lines only appear if data hits thresholds) ---
    if df['precipitation'].max() >= RAIN_MAX:
        ax1.axhline(y=RAIN_MAX, color='cyan', linestyle='--', alpha=0.5, label=f'RAIN ALERT (>{RAIN_MAX}mm)')
    
    if df['wind_speed_10m'].max() >= WIND_MAX:
        ax2.axhline(y=WIND_MAX, color='lime', linestyle='--', alpha=0.5, label=f'WIND ALERT (>{WIND_MAX}kmh)')

    if df['temperature_2m'].max() >= TEMP_MAX:
        ax2.axhline(y=TEMP_MAX, color='red', linestyle=':', alpha=0.7, label=f'HEAT ALERT (>{TEMP_MAX}°C)')

    if df['temperature_2m'].min() <= TEMP_MIN:
        ax2.axhline(y=TEMP_MIN, color='white', linestyle=':', alpha=0.7, label=f'FROST ALERT (<{TEMP_MIN}°C)')

    # --- FINAL FORMATTING ---
    plt.title(f"Nelson 5-Day Smart Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}", fontsize=14)
    ax1.set_xticks(df['time'][tick_indices])
    ax1.set_xticklabels([time_labels[i] for i in tick_indices])
    
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontweight='bold')
    ax2.set_ylabel('Wind (km/h) / Temp (°C)', color='#ff9900', fontweight='bold')

    # Legend (Combines both axes)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', frameon=True, facecolor='black')

    # Save logic
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    plt.tight_layout()
    
    # Save the timestamped version and the 'latest' version
    plt.savefig(f"weather_{timestamp}.png")
    plt.savefig("weather_latest.png")
    print(f"Success: weather_{timestamp}.png and weather_latest.png created.")

if __name__ == "__main__":
    print("Starting weather update...")
    cleanup_old_files(days_to_keep=5) 
    forecast_data = get_weather_data()
    generate_plot(forecast_data)
    print("Process finished.")
