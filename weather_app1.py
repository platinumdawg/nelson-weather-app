import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob

# 1. Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Richmond Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ["precipitation", "wind_speed_10m", "temperature_2m"],
        "wind_speed_unit": "kmh",
        "timezone": "Pacific/Auckland",
        "forecast_days": 5
    }
    
    try:
        # The library handles the connection and parsing
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Process hourly data
        hourly = response.Hourly()
        hourly_precipitation = hourly.Variables(0).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(1).ValuesAsNumpy()
        hourly_temperature_2m = hourly.Variables(2).ValuesAsNumpy()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            ),
            "precipitation": hourly_precipitation,
            "wind_speed_10m": hourly_wind_speed_10m,
            "temperature_2m": hourly_temperature_2m
        }

        return pd.DataFrame(data=hourly_data)
    except Exception as e:
        print(f"API Client Error: {e}")
        return None

def generate_plot(df):
    if df is None or df.empty:
        print("No data received. GitHub IP likely blocked.")
        return
        
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    ax1.plot(df['date'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['date'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['date'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    plt.title(f"Richmond 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated.")

if __name__ == "__main__":
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    data = get_weather_data()
    generate_plot(data)
