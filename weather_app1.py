import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import glob
import json

API_KEY = os.getenv('WEATHER_API_KEY')
LAT, LON = -41.3384, 173.1843

def get_weather_data():
    if not API_KEY:
        return None
        
    # 1. Build the target URL
    target_url = f"https://weatherapi.com{API_KEY}&q={LAT},{LON}&days=5"
    
    # 2. Wrap it in a Proxy (AllOrigins) to hide the GitHub IP
    proxy_url = f"https://allorigins.win{requests.utils.quote(target_url)}"
    
    try:
        # Request via proxy
        response = requests.get(proxy_url, timeout=30)
        
        if response.status_code == 200:
            # AllOrigins returns a JSON with a 'contents' string
            content_str = response.json()['contents']
            data = json.loads(content_str)
            
            hourly_list = []
            for day in data['forecast']['forecastday']:
                for hour in day['hour']:
                    hourly_list.append({
                        'time': hour['time'],
                        'temp_c': hour['temp_c'],
                        'wind_kph': hour['wind_kph'],
                        'precip_mm': hour['precip_mm']
                    })
            return pd.DataFrame(hourly_list)
        else:
            print(f"Proxy failed: {response.status_code}")
    except Exception as e:
        print(f"Connection failed even with proxy: {e}")
    return None

def generate_plot(df):
    if df is None or df.empty:
        print("No data received.")
        return
        
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    ax1.plot(df['time'], df['precip_mm'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_kph'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temp_c'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    plt.title(f"Richmond 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated via Proxy!")

if __name__ == "__main__":
    for f in glob.glob("weather_*.png"):
        if "latest" not in f:
            try: os.remove(f)
            except: pass
            
    data = get_weather_data()
    generate_plot(data)
