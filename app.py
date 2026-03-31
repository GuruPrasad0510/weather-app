import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px
from streamlit_lottie import st_lottie

API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="Weather Intelligence", layout="wide")

# 🌍 Auto location
def get_location():
    try:
        res = requests.get("http://ip-api.com/json/").json()
        return res['city']
    except:
        return "Bangalore"

# 🌦 Weather Data
def get_weather_data(location):
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()

        if data.get("cod") != "200":
            return pd.DataFrame(), None, None

        lat = data['city']['coord']['lat']
        lon = data['city']['coord']['lon']

        weather_list = []
        for entry in data['list']:
            weather_list.append({
                "Datetime": entry['dt_txt'],
                "Temp": entry['main']['temp'],
                "Humidity": entry['main']['humidity'],
                "Rain (mm)": entry.get('rain', {}).get('3h', 0),
                "Weather": entry['weather'][0]['description']
            })

        df = pd.DataFrame(weather_list)
        df['Datetime'] = pd.to_datetime(df['Datetime'])

        return df, lat, lon

    except:
        return pd.DataFrame(), None, None

# 📅 Summary
def daily_summary(df):
    df['Date'] = df['Datetime'].dt.date
    summary = df.groupby('Date').agg({
        'Temp': ['min', 'max', 'mean'],
        'Rain (mm)': 'sum'
    })
    summary.columns = ['Min Temp', 'Max Temp', 'Avg Temp', 'Total Rain']
    return summary.reset_index()

# 📥 Excel
def convert_to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

# 🌤 Emoji
def get_weather_emoji(desc):
    desc = desc.lower()
    if "rain" in desc: return "🌧"
    elif "cloud" in desc: return "☁"
    elif "clear" in desc: return "☀"
    elif "storm" in desc: return "⛈"
    else: return "🌤"

# 🎨 Theme
def get_theme(desc, hour):
    desc = desc.lower()
    is_night = hour >= 18 or hour <= 6

    if "rain" in desc:
        gradient = "#00c6ff, #0072ff"
        card = "rgba(0,114,255,0.2)"
    elif "cloud" in desc:
        gradient = "#757f9a, #d7dde8"
        card = "rgba(120,120,120,0.2)"
    elif "clear" in desc:
        gradient = "#f7971e, #ffd200"
        card = "rgba(255,200,0,0.2)"
    else:
        gradient = "#4facfe, #00f2fe"
        card = "rgba(0,200,255,0.2)"

    if is_night:
        gradient = "#141E30, #243B55"
        card = "rgba(20,30,50,0.5)"

    return gradient, card

# 🎥 Lottie
def load_lottie_url(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def get_lottie_animation(desc):
    desc = desc.lower()
    if "rain" in desc:
        return load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jmBauI.json")
    elif "cloud" in desc:
        return load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_KUFdS6.json")
    else:
        return load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_Stt1Rk.json")

# 🌍 SAFE GEO FUNCTION (FIXED)
def get_city_coords(city):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        res = requests.get(url).json()

        if not res:
            return None, None

        return res[0].get('lat'), res[0].get('lon')

    except:
        return None, None

# ================= UI =================

auto_location = get_location()

st.sidebar.title("⚙ Control Panel")
location = st.sidebar.text_input("📍 City", auto_location)
view = st.sidebar.radio("📊 View", ["Overview", "Trends", "Raw Data"])
multi_cities = st.sidebar.text_input("🌍 Compare Cities", "Bangalore, Mumbai, Delhi")

# ================= MAIN =================

if st.sidebar.button("Get Weather"):

    df, lat, lon = get_weather_data(location)

    if df.empty:
        st.error("Invalid city or API issue")
        st.stop()

    summary = daily_summary(df)

    current_temp = df['Temp'].iloc[0]
    current_weather = df['Weather'].iloc[0]
    emoji = get_weather_emoji(current_weather)

    hour = pd.Timestamp.now().hour
    gradient, card_color = get_theme(current_weather, hour)

    # 🌈 Animated Header
    st.markdown(f"""
    <style>
    .header {{
        text-align:center;
        font-size:42px;
        font-weight:bold;
        background: linear-gradient(270deg, {gradient});
        background-size:400% 400%;
        -webkit-background-clip:text;
        color:transparent;
        animation: move 6s infinite;
    }}
    @keyframes move {{
        0%{{background-position:0%}}
        50%{{background-position:100%}}
        100%{{background-position:0%}}
    }}
    </style>
    <div class="header">
    {emoji} {location} | {current_temp:.1f}°C — {current_weather.title()}
    </div>
    """, unsafe_allow_html=True)

    # 🎥 Animation
    st_lottie(get_lottie_animation(current_weather), height=150)

    # 🧊 Cards
    col1, col2, col3, col4 = st.columns(4)

    def card(title, value):
        return f"""
        <div style="background:{card_color};padding:20px;border-radius:15px;text-align:center;">
        <h4>{title}</h4><h2>{value}</h2></div>
        """

    col1.markdown(card("Avg Temp", f"{df['Temp'].mean():.1f}°C"), True)
    col2.markdown(card("Max Temp", f"{df['Temp'].max():.1f}°C"), True)
    col3.markdown(card("Min Temp", f"{df['Temp'].min():.1f}°C"), True)
    col4.markdown(card("Rain", f"{df['Rain (mm)'].sum():.1f} mm"), True)

    # 🌧 Radar
    tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"

    st.components.v1.html(f"""
    <div id="map" style="height:400px;"></div>
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <script>
    var map = L.map('map').setView([{lat}, {lon}], 6);
    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
    L.tileLayer('{tile_url}', {{opacity:0.6}}).addTo(map);
    </script>
    """, height=420)

    # 🌍 Multi-city (SAFE)
    cities = [c.strip() for c in multi_cities.split(",")]
    data = []

    for c in cities:
        la, lo = get_city_coords(c)

        if la is None:
            continue

        temp_df, _, _ = get_weather_data(c)

        if temp_df.empty:
            continue

        temp = temp_df['Temp'].iloc[0]

        data.append({
            "City": c,
            "lat": la,
            "lon": lo,
            "Temp": temp
        })

    mdf = pd.DataFrame(data)

    if not mdf.empty:
        fig = px.scatter_mapbox(mdf, lat="lat", lon="lon", size="Temp", color="Temp", hover_name="City")
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)

    # 📊 Views
    if view == "Overview":
        st.dataframe(summary)
    elif view == "Trends":
        st.plotly_chart(px.line(df, x="Datetime", y="Temp", markers=True))
    else:
        st.dataframe(df)

    # 📥 Download
    st.download_button("Download Excel", convert_to_excel(summary), "weather.xlsx")
