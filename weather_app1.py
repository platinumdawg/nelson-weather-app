import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import glob

# Richmond/Nelson, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    """Fetches 5-day forecast data from Met.no (Yr.no)."""
    api_url = "https://met.no"
    
    # Required custom User-Agent to prevent GitHub network blocks
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
            timeseries = data['properties']['timeseries']
            
            rows = []
            for entry in timeseries[:120]:  # Next ~5 days of hourly data
                row = {
                    'time': entry['time'],
                    'temp': entry['data']['instant']['details']['air_temperature'],
                    'wind': entry['data']['instant']['details']['wind_speed'] * 3.6, # m/s to km/h
                    'rain': entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0)
                }
                rows.append(row)
            
            return pd.DataFrame(rows)
        else:
            print(f"API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Network error: {e}")
        return None

def generate_plot(df):
    """Generates the weather chart with custom scales and date formatting."""
    if df is None or df.empty:
        print("CRITICAL: Failed to retrieve data.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    
    # Secondary axis for Rain
    ax2 = ax1.twinx()

    # LEFT AXIS: Temp (solid) and Wind (dashed)
    ax1.plot(df['time'], df['temp'], color='#ff9900', linewidth=3, label='Temp (°C)')
    ax1.plot(df['time'], df['wind'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')
    ax1.set_ylabel('Temp (°C) & Wind (km/h)', fontsize=12)
    ax1.grid(True, alpha=0.1)

    # RIGHT AXIS: Rain (Blue line with max 20mm)
    ax2.plot(df['time'], df['rain'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.set_ylabel('Rainfall (mm)', color='#44aaff', fontsize=12)
    ax2.set_ylim(0, 20)  # Lock max rain to 20mm
    ax2.fill_between(df['time'], df['rain'], color='#44aaff', alpha=0.15)

    # X-AXIS: Format to show Day (Mon, Tue) + Date
    # Removed 2026/year as requested
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %b'))
    plt.xticks(rotation=0)

    # Title and Legend
    plt.title(f"Nelson/Richmond Forecast\nUpdated: {datetime.now().strftime('%a %d %b %H:%M')}", fontsize=16)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success! Created 'weather_latest.png'.")

if __name__ == "__main__":
    # Clean up old images before running
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    weather_df = get_weather_data()
    generate_plot(weather_df)
