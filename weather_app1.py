import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob
import json
import urllib.parse

# Richmond, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    # 1. The Direct URL
    base_url = "https://open-meteo.com"
    params = f"latitude={LAT}&longitude={LON}&hourly=precipitation,wind_speed_10m,temperature_2m&wind_speed_unit=kmh&timezone=Pacific/Auckland&forecast_days=5"
    full_url = f"{base_url}?{params}"
    
    # 2. Try Direct Connection First
    try:
        print("Attempting direct connection...")
        response = requests.get(full_url, timeout=15)
        if response.status_code == 200:
            return pd.DataFrame(response.json()['hourly'])
    except Exception as e:
        print(f"Direct connection blocked: {e}")

    # 3. If Direct Fails, Try The Proxy (The Bypass)
    try:
        print("Attempting bypass via proxy...")
        # We use a different proxy service (Corsproxy.io) for better reliability
        proxy_url = f"https://corsproxy.io?{urllib.parse.quote(full_url)}"
        response = requests.get(proxy_url, timeout=20)
        
        if response.status_code == 200:
            return pd.DataFrame(response.json()['hourly'])
        else:
            print(f"Proxy also failed with status: {response.status_code}")
    except Exception as e:
        print(f"Bypass failed: {e}")
        
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: All connection methods failed. GitHub's network is fully blocked.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

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
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    data = get_weather_data()
    generate_plot(data)

