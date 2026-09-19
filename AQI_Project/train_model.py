import os, json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

os.makedirs("model", exist_ok=True)
np.random.seed(42)
N = 1500

# ── Realistic pollutant generation (Indian city ranges) ──────────────────────
pm25 = np.random.lognormal(mean=3.8, sigma=0.8, size=N).clip(5, 500)
pm10 = (pm25 * np.random.uniform(1.5, 2.5, N) + np.random.normal(0, 20, N)).clip(10, 600)
no2  = np.random.lognormal(mean=3.5, sigma=0.6, size=N).clip(5, 400)
so2  = np.random.lognormal(mean=2.5, sigma=0.7, size=N).clip(2, 200)
co   = np.random.lognormal(mean=0.2, sigma=0.8, size=N).clip(0.1, 50)
o3   = np.random.lognormal(mean=3.2, sigma=0.5, size=N).clip(5, 300)

# ── CPCB Sub-index formula ────────────────────────────────────────────────────
def sub_index(Cp, bps):
    for BPLo, BPHi, ILo, IHi in bps:
        if BPLo <= Cp <= BPHi:
            return ((IHi - ILo) / (BPHi - BPLo)) * (Cp - BPLo) + ILo
    return 500

PM25_BP = [(0,30,0,50),(30,60,51,100),(60,90,101,200),(90,120,201,300),(120,250,301,400),(250,500,401,500)]
PM10_BP = [(0,50,0,50),(50,100,51,100),(100,250,101,200),(250,350,201,300),(350,430,301,400),(430,600,401,500)]
NO2_BP  = [(0,40,0,50),(40,80,51,100),(80,180,101,200),(180,280,201,300),(280,400,301,400),(400,800,401,500)]
SO2_BP  = [(0,40,0,50),(40,80,51,100),(80,380,101,200),(380,800,201,300),(800,1600,301,400),(1600,2100,401,500)]
CO_BP   = [(0,1,0,50),(1,2,51,100),(2,10,101,200),(10,17,201,300),(17,34,301,400),(34,50,401,500)]
O3_BP   = [(0,50,0,50),(50,100,51,100),(100,168,101,200),(168,208,201,300),(208,748,301,400),(748,1000,401,500)]

aqi_list = []
for i in range(N):
    aqi_list.append(max(
        sub_index(pm25[i], PM25_BP),
        sub_index(pm10[i], PM10_BP),
        sub_index(no2[i],  NO2_BP),
        sub_index(so2[i],  SO2_BP),
        sub_index(co[i],   CO_BP),
        sub_index(o3[i],   O3_BP),
    ))

df = pd.DataFrame({"PM2.5":pm25,"PM10":pm10,"NO2":no2,"SO2":so2,"CO":co,"O3":o3,"AQI":aqi_list})

X = df[["PM2.5","PM10","NO2","SO2","CO","O3"]]
y = df["AQI"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(f"R²  = {r2_score(y_test, y_pred):.4f}")
print(f"MAE = {mean_absolute_error(y_test, y_pred):.2f}")

joblib.dump(model, "model/aqi_model.pkl")

# Save feature importances
importances = dict(zip(["PM2.5","PM10","NO2","SO2","CO","O3"],
                       model.feature_importances_.tolist()))
with open("model/feature_importances.json", "w") as f:
    json.dump(importances, f)

print("Model & feature importances saved! Done.")