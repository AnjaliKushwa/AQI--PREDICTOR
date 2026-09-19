import streamlit as st
import numpy as np
import pickle
import os

# Page setup
st.set_page_config(page_title="AQI Predictor", page_icon="🌫️")

st.title("🌫️ Air Quality Index (AQI) Predictor")
st.write("Enter pollution values below:")

# Model path (safe)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
model_path = os.path.join(BASE_DIR, "model", "aqi_model.pkl")

# Load model safely
try:
    model = pickle.load(open("../model/aqi_model.pkl", "rb"))
except Exception as e:
    st.error(f"Model load nahi ho pa raha ❌: {e}")
    st.stop()

# Inputs
pm25 = st.number_input("PM2.5")
pm10 = st.number_input("PM10")
no2 = st.number_input("NO2")
co = st.number_input("CO")

# Prediction
if st.button("Predict AQI"):
    input_data = np.array([[pm25, pm10, no2, co]])
    prediction = model.predict(input_data)[0]

    st.success(f"Predicted AQI: {prediction:.2f}")

    # Category
    if prediction <= 50:
        st.success("Good 😊")
    elif prediction <= 100:
        st.warning("Moderate 😐")
    elif prediction <= 200:
        st.error("Poor 😷")
    else:
        st.error("Hazardous ☠️")