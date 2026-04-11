import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

def get_weather_data():
    url = "https://open-meteo.com"
    params = {
        "latitude": LAT, "longitude": LON,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "wind_speed_unit": "kmh", "timezone": "Pacific/Auckland", "forecast_days": 5
    }
    
    # 1. Setup retries to handle unstable GitHub runner connections
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        # Use a unique User-Agent to avoid generic bot blocks
        headers = {'User-Agent': 'RichmondWeatherBot/1.0 (Contact: your-email@example.com)'}
        response = session.get(url, params=params, headers=headers, timeout=15)
        
        # 2. Check if we actually got a successful response
        if response.status_code == 200:
            return pd.DataFrame(response.json()['hourly'])
        
        # 3. DEBUG: If it fails, print the status and the first 200 chars of the error
        # This will tell you if you are BLOCKED (403) or RATE LIMITED (429)
        print(f"API Error {response.status_code}: {response.text[:200]}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    return None



def generate_plot(df):
    if df is None: return
    df['time'] = pd.to_datetime(df['time'])
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()

    # Create Day/Night Labels
    def format_time(t):
        if t.hour == 12: return f"{t.strftime('%a')}\nDay"
        if t.hour == 0: return f"{t.strftime('%a')}\nNight"
        return ""
    
    time_labels = [format_time(t) for t in df['time']]
    tick_indices = [i for i, label in enumerate(time_labels) if label != ""]

    # Plot Lines
    ax1.plot(df['time'], df['precipitation'], color='#44aaff', linewidth=2, label='Rain (mm/h)')
    ax2.plot(df['time'], df['wind_speed_10m'], color='#00ff00', linewidth=2, label='Wind (km/h)')
    ax2.plot(df['time'], df['temperature_2m'], color='#ff9900', linewidth=2.5, label='Temp (°C)')

    # Alerts (Only if triggered)
    if df['precipitation'].max() >= RAIN_MAX: ax1.axhline(y=RAIN_MAX, color='cyan', linestyle='--')
    if df['wind_speed_10m'].max() >= WIND_MAX: ax2.axhline(y=WIND_MAX, color='lime', linestyle='--')

    plt.title(f"Richmond 5-Day Forecast\nUpdated: {datetime.now().strftime('%d %b %H:%M')}")
    ax1.set_xticks(df['time'][tick_indices]); ax1.set_xticklabels([time_labels[i] for i in tick_indices])
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')

    plt.tight_layout()
    plt.savefig("weather_latest.png")
    print("Success: weather_latest.png updated.")

if __name__ == "__main__":
    # Clean up old files if they exist
    for f in glob.glob("weather_*.png"):
        if "latest" not in f: os.remove(f)
    
    data = get_weather_data()
    generate_plot(data)
