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
    try:
        url = f"https://open-meteo.com{lat}&longitude={lon}&daily=precipitation_sum,wind_speed_10m_max&wind_speed_unit=kmh&timezone=auto"
        res = requests.get(url, timeout=5, verify=False).json()
        daily_data = res['daily']
        raw_dates = daily_data['time'][:5]
        forecast_rain = daily_data['precipitation_sum'][:5]
        forecast_wind = daily_data['wind_speed_10m_max'][:5]
        formatted_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%d") for d in raw_dates]
    except:
        return

    try:
        end = datetime.now()
        start = end - timedelta(days=730)
        data = Daily(nelson_loc, start, end).fetch()
        if data is None or data.empty:
            data = pd.DataFrame({'prcp': np.random.exponential(5, 100), 'wspd': np.random.normal(15, 5, 100)})
        data['is_storm'] = ((data['prcp'] > 10) & (data['wspd'] > 35)).astype(int)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(data[['prcp', 'wspd']].fillna(0).values, data['is_storm'])
    except:
        return

    storm_probs = []
    for i in range(len(raw_dates)):
        prob = model.predict_proba([[forecast_rain[i], forecast_wind[i]]])
        storm_probs.append(prob[0][1] if prob.shape[1] > 1 else 0.0)

    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(12, 7))
    bars = ax1.bar(formatted_dates, storm_probs, color='#ff4444', alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(formatted_dates, forecast_rain, color='#44aaff', marker='o')
    ax2.plot(formatted_dates, forecast_wind, color='#00ff00', linestyle='--')
    
    plt.tight_layout()
    plt.savefig('nelson_forecast.png')

if __name__ == "__main__":
    run_nelson_weather()
