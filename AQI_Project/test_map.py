import plotly.graph_objects as go
import random

def test_map():
    dark = True
    lat, lon = 28.6139, 77.2090
    zones = ["North", "South", "East", "West", "Central", "Industrial Area", "Residential", "Commercial", "City Center"]
    lats = [lat + random.uniform(-0.08, 0.08) for _ in range(8)] + [lat]
    lons = [lon + random.uniform(-0.08, 0.08) for _ in range(8)] + [lon]
    
    base_aqi = 150
    aqis = [max(10, base_aqi + random.uniform(-50, 80)) for _ in range(9)]
    temps = [random.uniform(25, 38) for _ in range(9)]
    humids = [random.uniform(40, 80) for _ in range(9)]
    
    hover_text = []
    for i in range(9):
        hover_text.append(f"<b>{zones[i]}</b><br>AQI: {int(aqis[i])}<br>Temp: {temps[i]:.1f}°C<br>Humidity: {humids[i]:.0f}%")
        
    fig = go.Figure(go.Densitymapbox(
        lat=lats, lon=lons, z=aqis, radius=40,
        colorscale="RdYlGn_r", zmin=0, zmax=500,
        text=hover_text, hoverinfo="text"
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter" if dark else "carto-positron",
            center=dict(lat=lat, lon=lon),
            zoom=10
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
    )
    print("Success")

test_map()
