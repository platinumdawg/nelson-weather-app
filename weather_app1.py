import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob

# Richmond/Nelson, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    # Met.no API (Yr.no) is very stable for GitHub runners
    api_url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    
    # REQUIRED: Use a unique User-Agent to avoid the 'char 0' block
    # format: "AppName/Version contact@email.com"
    headers = {
        'User-Agent': 'NelsonWeatherBot/1.0 yourname@example.com'
    }
    
    params = {
        'lat': round(LAT, 4),
        'lon': round(LON, 4)
    }

    try:
        print(f"Connecting to Met.no for Richmond weather...")
        response = requests.get(api_url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            # Extracting the timeseries data
            timeseries = data['properties']['timeseries']
            
            rows = []
            for entry in timeseries[:120]:  # Get next 5 days (approx 120 hours)
                row = {
                    'time': entry['time'],
                    'temp': entry['data']['instant']['details']['air_temperature'],
                    'wind': entry['data']['instant']['details']['wind_speed'] * 3.6, # Convert m/s to km/h
                    'rain': entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0)
                }
                rows.append(row)
            
            return pd.DataFrame(rows)
        else:
            print(f"Block detected: {response.status_code}")
            print(f"Content: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"Network error: {e}")
        return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: Failed to retrieve data. Check your User-Agent header.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    ax1.plot(df['time'], df['rain'], color='#44aaff', alpha=0.6, label='Rain (mm/h)')
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontsize=12)
    ax1.set_ylim(0, 20)
    
   
    ax2.plot(df['time'], df['wind'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')
    ax2.set_ylabel('Wind (km/h)', color='#ff9900', fontsize=12)

    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))
    ax3.scatter(df['time'], df['temp'], color='#ff9900', s=30, label='Temp (°C)')
    ax3.set_ylabel('Temp (°C)', color='#ff9900', fontsize=12)

    plt.title(f"Nelson/Richmond Forecast (Met.no Data)\nUpdated: {datetime.now().strftime('%d %b %H:%M')}", fontsize=16)
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success! Created 'weather_latest.png'.")

if __name__ == "__main__":
    # Clean up old local png files
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    weather_df = get_weather_data()
    generate_plot(weather_df)
