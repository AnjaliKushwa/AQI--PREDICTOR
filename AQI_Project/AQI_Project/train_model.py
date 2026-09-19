import os
os.makedirs("model", exist_ok=True)

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Dummy data (abhi real dataset ki tension nahi 😄)
data = {
    "PM2.5":[50,120,200,80],
    "PM10":[80,180,300,100],
    "NO2":[20,40,60,30],
    "SO2":[5,10,20,7],
    "CO":[0.5,1.2,2.0,0.7],
    "O3":[10,30,50,20],
    "AQI":[100,250,400,150]
}

df = pd.DataFrame(data)

X = df[['PM2.5','PM10','NO2','SO2','CO','O3']]
y = df['AQI']

model = RandomForestRegressor()
model.fit(X,y)

joblib.dump(model,"model/aqi_model.pkl")
print("Model ready ✅")