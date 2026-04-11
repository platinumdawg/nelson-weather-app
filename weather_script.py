import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from meteostat import Point, daily
from sklearn.ensemble import RandomForestClassifier
import warnings

# 1. SETUP
warnings.filterwarnings("ignore")
lat, lon = -41.298, 173.226 # Nelson Coordinates
nelson_loc = Point(lat, lon)

def run_nelson_weather():
    print(f"--- NELSON DARK MODE PREDICTOR ({datetime.now().strftime('%H:%M')}) ---")

    # 2. FETCH 5-DAY FORECAST
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,wind_speed_10m_max&wind_speed_unit=kmh&timezone=auto"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5, verify=False).json()
        
        daily_data = res['daily']
        raw_dates = daily_data['time'][:5]
        forecast_rain = daily_data['precipitation_sum'][:5]
        forecast_wind = daily_data['wind_speed_10m_max'][:5]
        
        # Convert YYYY-MM-DD to "Mon 12" format
        formatted_dates = [datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%d") for d in raw_dates]
        
    except Exception as e:
        print(f"(!) Connection failed: {e}")
        return

    # 3. ML TRAINING
    try:
        end = datetime.now()
        start = end - timedelta(days=730)
        data = daily(nelson_loc, start, end).fetch()

        if data is None or data.empty:
            data = pd.DataFrame({
                'prcp': np.random.exponential(5, 100), 
                'wspd': np.random.normal(15, 5, 100)
            })

        data['is_storm'] = ((data['prcp'] > 10) & (data['wspd'] > 35)).astype(int)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(data[['prcp', 'wspd']].fillna(0).values, data['is_storm'])

    except Exception as e:
        print(f"Training Error: {e}")
        return

    # 4. PREDICT & VISUALIZE
    storm_probs = []
    for i in range(len(raw_dates)):
        prob = model.predict_proba([[forecast_rain[i], forecast_wind[i]]])
        storm_probs.append(prob[0][1] if prob.shape[1] > 1 else 0.0)

    # --- DARK THEME PLOTTING ---
    plt.style.use('dark_background') # Instant Dark Mode
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Background color tweaking (optional, for 'blacker' black)
    fig.patch.set_facecolor('black')
    ax1.set_facecolor('black')

    # Left Axis: Risk Bars
    bars = ax1.bar(formatted_dates, storm_probs, color='#ff4444', alpha=0.3, label='Storm Risk')
    ax1.set_ylabel('Storm Probability', color='#ff4444', fontweight='bold')
    ax1.set_ylim(0, 1.1)
    ax1.tick_params(axis='y', colors='#ff4444')

    # Right Axis: Weather Lines
    ax2 = ax1.twinx()
    line1, = ax2.plot(formatted_dates, forecast_rain, color='#44aaff', marker='o', linewidth=2, label='Rain (mm)')
    line2, = ax2.plot(formatted_dates, forecast_wind, color='#00ff00', linestyle='--', marker='x', linewidth=2, label='Wind (km/h)')
    
    ax2.set_ylabel('Intensity', color='white', fontweight='bold')
    ax2.tick_params(axis='y', colors='white')

    # --- DATA LABELS (The requested addition) ---
    for i, txt in enumerate(formatted_dates):
        # Rain Label (Blue) - Slight offset above point
        ax2.text(i, forecast_rain[i] + 1, f"{forecast_rain[i]}mm", 
                 color='#44aaff', ha='center', fontsize=9, fontweight='bold')
        
        # Wind Label (Green) - Slight offset below point
        ax2.text(i, forecast_wind[i] - 2, f"{forecast_wind[i]}k", 
                 color='#00ff00', ha='center', fontsize=9, fontweight='bold')

    # Title & Layout
    plt.title('Nelson Forecast: Risk vs Intensity', color='white', fontsize=14, pad=20)
    
    # Legend
    lines = [bars, line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', facecolor='#333', edgecolor='white')

    ply.tight_layout()
    plt.savefig('nelson_forecast.png')

if __name__ == "__main__":
    run_nelson_weather()
