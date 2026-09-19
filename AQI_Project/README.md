# 🌍 AQI Predictor Pro

A modern, intelligent, and citizen-friendly web application designed to predict the Air Quality Index (AQI) based on multiple pollutant levels and provide actionable, easy-to-understand health advisories.

## 🚨 The Problem Statement
Air pollution is a silent crisis affecting millions worldwide, especially in rapidly urbanizing regions. While technical data (like PM2.5, NO2, or SO2 levels) is frequently collected by environmental monitoring stations, **the common person often struggles to interpret what these numbers mean for their health.** 

Scientific jargon, complex metrics, and technical index numbers fail to answer the most critical questions:
- *Is it safe for my child to play outside today?*
- *Should my elderly parents go for their morning walk?*
- *What do these specific gases actually do to my lungs?*

**AQI Predictor Pro** bridges the gap between raw scientific environmental data and everyday human health. It transforms complex pollutant data into an accurate predictive AQI score using Machine Learning, and translates that score into actionable, plain-language health guidance for the general public.

---

## ✨ Key Features

### 1. 🧠 ML-Powered Prediction
- Predicts accurate AQI using a trained Machine Learning model based on the Central Pollution Control Board (CPCB) standards.
- Evaluates 6 key pollutants: **PM2.5, PM10, NO2, SO2, CO, and O3**.

### 2. 🧑‍⚕️ Plain-Language Health Advisory
- **No Science Degree Needed**: Translates complex AQI categories into simple language explaining exactly what the air quality means for you.
- **Symptom Tracker**: Lists possible symptoms you might feel based on current exposure.
- **Time-of-Day Guidance**: Tells you the best times to go outside and when you should absolutely stay indoors.
- **Group-Specific Alerts**: Tailored advice for vulnerable groups including Children, the Elderly, and Asthma/Heart patients.

### 3. 🗺️ City Heat Sink & Hotspot Map
- Interactive map showing a simulated representation of Temperature, Humidity, and Pollution hotspots across different zones in the selected city.
- Visually identify areas like Industrial Zones vs. City Centers and their respective pollution intensities.

### 4. 📖 Educational Pollutant Guide
- Breaks down every pollutant (PM2.5, NO2, etc.) explaining:
  - What it is
  - Where it comes from
  - Why it is harmful
  - How it feels at low, high, and severe exposure levels
- Compares current measured levels against absolute safe limits.

### 5. 📊 Advanced Visualizations
- **AQI Speedometer Gauge**: A quick visual representation of the current AQI category.
- **Pollutant Radar Chart**: Shows a holistic view of all pollutants relative to their maximum limits.
- **Feature Importance**: See exactly which pollutant is driving the current AQI the hardest.

### 6. 🌗 Premium UI & User Experience
- Fully responsive layout with a beautiful Dark Mode / Light Mode toggle.
- Session-based history tracker to compare cities side-by-side.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed on your system.

### Installation & Setup
1. Clone this repository or download the project files.
2. Install the required dependencies:
   ```bash
   pip install streamlit numpy pandas scikit-learn plotly joblib
   ```
3. (Optional) Retrain the Machine Learning model if you have updated data:
   ```bash
   python train_model.py
   ```

### Running the Application
To launch the interactive dashboard, run the following command from the project root directory:

```bash
streamlit run frontend/app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🛠️ Technology Stack
- **Frontend / UI**: Streamlit (Python)
- **Data Visualization**: Plotly Graph Objects
- **Machine Learning**: Scikit-Learn (Random Forest / Decision Trees)
- **Styling**: Custom CSS injected via Streamlit markdown

---

## 🤝 Purpose
This project is built to democratize environmental data. Clean air is a human right, and understanding the air we breathe should not require an environmental science degree. AQI Predictor Pro empowers citizens to make informed decisions about their daily activities and health.
