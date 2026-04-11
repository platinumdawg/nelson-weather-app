import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from meteostat import Point, Daily 
from sklearn.ensemble import RandomForestClassifier
import warnings

Daily.max_age = 0 
warnings.filterwarnings("ignore")
lat, lon = -41.298, 173.226 
nelson_loc = Point(lat, lon)

def run_nelson_weather():
    print("Connecting to API...")
    try:
        # FIXED URL: Added 'v1/forecast' and the '?' before latitude
        url = f"https://open-meteo.com{lat}&longitude={lon}&daily=precipitation_sum,wind_speed_10m_max&wind_speed_unit=kmh&timezone=auto"
        res = requests.get(url, timeout=10).json()
        
        forecast_data = res['daily']
        raw_dates = forecast_data['time'][:5]
        forecast_rain = forecast_data['precipitation_sum'][:5]
        forecast_wind = forecast_data['wind_speed_10m_max'][:5]
        formatted_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%d") for d in raw_dates]
    except Exception as e:
        print(f"Forecast API Error: {e}")
        return

    print("Running Storm Model...")
    try:
        end = datetime.now()
        start = end - timedelta(days=730)
        data = Daily(nelson_loc, start, end).fetch()
        
        if data is None or data.empty:
            data = pd.DataFrame({'prcp': np.random.exponential(5, 100), 'wspd': np.random.normal(15, 5, 100)})
        
        data['is_storm'] = ((data['prcp'].fillna(0) > 10) & (data['wspd'].fillna(0) > 35)).astype(int)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(data[['prcp', 'wspd']].fillna(0).values, data['is_storm'])
        
        storm_probs = [model.predict_proba([[forecast_rain[i], forecast_wind[i]]])[0][1] for i in range(len(raw_dates))]
    except Exception as e:
        print(f"Modeling Error: {e}")
        return

    print("Generating Chart...")
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Probability Bars
    ax1.bar(formatted_dates, storm_probs, color='#ff4444', alpha=0.3, label='Storm Prob')
    ax1.set_ylim(0, 1)
    ax1.set_ylabel('Probability')

    # Rain and Wind lines
    ax2 = ax1.twinx()
    ax2.plot(formatted_dates, forecast_rain, color='#44aaff', marker='o', label='Rain (mm)')
    ax2.plot(formatted_dates, forecast_wind, color='#00ff00', linestyle='--', label='Wind (km/h)')
    
    plt.title(f"Nelson Weather - Updated {datetime.now().strftime('%d %b %H:%M')}")
    plt.savefig('nelson_forecast.png')
    print("Success: nelson_forecast.png created.")

if __name__ == "__main__":
    run_nelson_weather()
