import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import matplotlib.pyplot as plt
from datetime import datetime, timedelta  # <--- THIS WAS MISSING
import os
import glob

# Fix for the "Buffer/unpack_from" error: Clear cache every run
if os.path.exists(".cache.sqlite"):
    os.remove(".cache.sqlite")

# Setup Open-Meteo Client
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Configuration
LOCATIONS = [
    {"name": "Nelson Central", "lat": -41.2706, "lon": 173.2840},
    {"name": "Richmond", "lat": -41.3384, "lon": 173.1843},
    {"name": "Nelson Airport", "lat": -41.298, "lon": 173.226}
]

RAIN_MAX, WIND_MAX, TEMP_MAX, TEMP_MIN = 10.0, 20.0, 20.0, 0.0

def cleanup_old_files(days_to_keep=5):
    """Deletes png files older than 5 days."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    for f in glob.glob("weather_*.png"):
        if "latest" in f: continue
        try:
            if datetime.fromtimestamp(os.path.getmtime(f)) < cutoff:
                os.remove(f)
                print(f"Deleted old file: {f}")
        except: pass

def get_weather_data():
    url = "https://open-meteo.com"
    all_dfs = []
    for loc in LOCATIONS:
        params = {
            "latitude": loc["lat"], "longitude": loc["lon"],
            "hourly": ["precipitation", "wind_speed_10m", "temperature_2m"],
            "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
        }
        try:
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]
            hourly = response.Hourly()
            
            # Time handling
            time_start = pd.to_datetime(hourly.Time(), unit="s", utc=True)
            time_end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
            times = pd.date_range(start=time_start, end=time_end, freq='H', inclusive='left').tz_convert("Pacific/Auckland")

            df = pd.DataFrame({
                "time": times,
                "precipitation": hourly.Variables(0).ValuesAsNumpy(),
                "wind_speed_10m": hourly.Variables(1).ValuesAsNumpy(),
                "temperature_2m": hourly.Variables(2).ValuesAsNumpy()
            })
            all_dfs.append(df)
            print(f"Fetched {loc['name']}")
        except Exception as e: print(f"Failed {loc['name']}: {e}")

    return pd.concat(all_dfs).groupby('time').mean().reset_index() if all_dfs else None

def generate_plot(df):
    if df is None: return
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    def format_time(t):
        if t.hour == 12: return f"{t.strftime('%a')}\nDay"
        if t.hour == 0: return f"{t.strftime('%a')}\nNight"
        return ""
    
    time_labels = [format_time(t) for t in df['time']]
    tick_indices = [i for i, label in enumerate(time_labels) if label != ""]

    # Plotting
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    # Alerts (Visible only if triggered)
    if df['precipitation'].max() >= RAIN_MAX: ax1.axhline(y=RAIN_MAX, color='cyan', linestyle='--', alpha=0.5, label='RAIN ALERT')
    if df['wind_speed_10m'].max() >= WIND_MAX: ax2.axhline(y=WIND_MAX, color='lime', linestyle='--', alpha=0.5, label='WIND ALERT')
    if df['temperature_2m'].max() >= TEMP_MAX: ax2.axhline(y=TEMP_MAX, color='red', linestyle=':', alpha=0.7, label='HEAT ALERT')
    if df['temperature_2m'].min() <= TEMP_MIN: ax2.axhline(y=TEMP_MIN, color='white', linestyle=':', alpha=0.7, label='FROST ALERT')

    plt.title(f"Nelson 5-Day Smart Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    ax1.set_xticks(df['time'][tick_indices])
    ax1.set_xticklabels([time_labels[i] for i in tick_indices])
    ax1.set_ylabel('Rain (mm)', color='#44aaff')
    ax2.set_ylabel('Wind / Temp', color='#ff9900')

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left', frameon=True, facecolor='black')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    plt.tight_layout()
    plt.savefig(f"weather_{timestamp}.png")
    plt.savefig("weather_latest.png")
    print(f"Saved weather_{timestamp}.png")

if __name__ == "__main__":
    cleanup_old_files()
    data = get_weather_data()
    generate_plot(data)
