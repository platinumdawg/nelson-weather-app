import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from meteostat import Point, Daily 
from sklearn.ensemble import RandomForestClassifier
import warnings
import os

# Setup
Daily.max_age = 0 
warnings.filterwarnings("ignore")
lat, lon = -41.298, 173.226 
nelson_loc = Point(lat, lon)

def run_nelson_weather():
    print("Fetching forecast data...")
    try:
        # Fixed the URL string formatting
        url = f"https://open-meteo.com{lat}&longitude={lon}&daily=precipitation_sum,wind_speed_10m_max&wind_speed_unit=kmh&timezone=auto"
        res = requests.get(url, timeout=10).json()
        daily_data = res['daily']
        raw_dates = daily_data['time'][:5]
        forecast_rain = daily_data['precipitation_sum'][:5]
        forecast_wind = daily_data['wind_speed_10m_max'][:5]
        formatted_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%d") for d in raw_dates]
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return

    print("Training storm model...")
    try:
        end = datetime.now()
        start = end - timedelta(days=730)
        data = Daily(nelson_loc, start, end).fetch()
        
        if data is None or data.empty:
            # Fallback data if API fails
            data = pd.DataFrame({
                'prcp': np.random.exponential(5, 100), 
                'wspd': np.random.normal(15, 5, 100)
            })
            
        data['is_storm'] = ((data['prcp'].fillna(0) > 10) & (data['wspd'].fillna(0) > 35)).astype(int)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        X = data[['prcp', 'wspd']].fillna(0).values
        model.fit(X, data['is_storm'])
        
        storm_probs = []
        for i in range(len(raw_dates)):
            prob = model.predict_proba([[forecast_rain[i], forecast_wind[i]]])
            storm_probs.append(prob[0][1] if prob.shape[1] > 1 else 0.0)
    except Exception as e:
        print(f"Error in modeling: {e}")
        return

    print("Generating chart...")
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Probabilities
    ax1.bar(formatted_dates, storm_probs, color='#ff4444', alpha=0.3, label='Storm Prob')
    ax1.set_ylabel('Storm Probability', color='#ff4444')
    ax1.set_ylim(0, 1)

    # Rain and Wind
    ax2 = ax1.twinx()
    ax2.plot(formatted_dates, forecast_rain, color='#44aaff', marker='o', label='Rain (mm)')
    ax2.plot(formatted_dates, forecast_wind, color='#00ff00', linestyle='--', label='Wind (km/h)')
    ax2.set_ylabel('Rain / Wind Scale')
    
    plt.title(f"Nelson Forecast - Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
    
    plt.tight_layout()
    plt.savefig('nelson_forecast.png')
    print("Success! Saved as nelson_forecast.png")

if __name__ == "__main__":
    run_nelson_weather()
