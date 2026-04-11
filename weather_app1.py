import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob
import matplotlib.dates as mdates

# Richmond/Nelson, NZ Coordinates
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    api_url = "https://met.no"
    headers = {'User-Agent': 'NelsonWeatherBot/1.0 yourname@example.com'}
    params = {'lat': round(LAT, 4), 'lon': round(LON, 4)}

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            timeseries = data['properties']['timeseries']
            rows = []
            for entry in timeseries[:72]: 
                row = {
                    'time': entry['time'],
                    'wind': entry['data']['instant']['details']['wind_speed'] * 3.6,
                    'rain': entry['data'].get('next_1_hours', {}).get('details', {}).get('precipitation_amount', 0)
                }
                rows.append(row)
            return pd.DataFrame(rows)
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_plot(df):
    if df is None or df.empty:
        print("CRITICAL: No data.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    
    # Create Second Axis for Wind
    ax2 = ax1.twinx() 

    # 1. Plot Rain (Bars)
    rain_bars = ax1.bar(df['time'], df['rain'], color='#44aaff', alpha=0.4, width=0.03, label='Rain (mm)')
    ax1.set_ylabel('Rain (mm)', color='#44aaff', fontsize=12)
    ax1.set_ylim(0, max(df['rain'].max() + 2, 10))

    # Add Rain Labels on Peaks
    rain_labels = [f'{v:.1f}' if v > 0.4 else '' for v in df['rain']]
    ax1.bar_label(rain_bars, labels=rain_labels, padding=3, color='#44aaff', fontsize=9)

    # 2. Plot Wind (Green Dashed Line)
    ax2.plot(df['time'], df['wind'], color='#00ff00', linewidth=1.5, linestyle='--', label='Wind (km/h)')
    ax2.set_ylabel('Wind (km/h)', color='#00ff00', fontsize=12)

    # --- Formatting Fixes ---
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=4))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d\n%H:%M'))
    ax1.grid(True, which='major', linestyle='--', alpha=0.2, color='gray')
    
    # Rotate dates and align
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.title(f"Nelson/Richmond Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}", fontsize=16)
    
    # Save specifically as weather_latest.png
    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success! Created 'weather_latest.png'.")

if __name__ == "__main__":
    weather_df = get_weather_data()
    generate_plot(weather_df)

