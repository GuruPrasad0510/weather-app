import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px
import time

# 🔑 API KEY
API_KEY = os.getenv("API_KEY")  # or replace with string

st.set_page_config(page_title="Weather Intelligence", layout="wide")

# ------------------ SESSION STATE ------------------

if "page" not in st.session_state:
    st.session_state.page = "home"

if "location" not in st.session_state:
    st.session_state.location = ""

if "recent" not in st.session_state:
    st.session_state.recent = []

# ------------------ FUNCTIONS ------------------

def get_weather_data(location):
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
        data = requests.get(url, timeout=5).json()

        if data.get("cod") != "200":
            return pd.DataFrame(), None

        rows = []
        for e in data['list']:
            rows.append({
                "Datetime": e['dt_txt'],
                "Temp": e['main']['temp'],
                "Feels": e['main']['feels_like'],
                "Humidity": e['main']['humidity'],
                "Wind": e['wind']['speed'],
                "Rain": e.get('rain', {}).get('3h', 0),
                "Weather": e['weather'][0]['description'],
                "Icon": e['weather'][0]['icon']
            })

        df = pd.DataFrame(rows)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        return df, data['list'][0]

    except:
        return pd.DataFrame(), None


def convert_to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


def add_to_recent(city):
    if city not in st.session_state.recent:
        st.session_state.recent.insert(0, city)
        st.session_state.recent = st.session_state.recent[:5]


# ------------------ UI STYLE ------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0b1d3a, #111827);
    color: white;
}

.hero {
    text-align: center;
    padding: 30px;
}

.hero-temp {
    font-size: 70px;
    font-weight: 700;
}

.hero-desc {
    font-size: 22px;
    color: #cbd5e1;
}

.card {
    background: #1e293b;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}

.section {
    font-size: 22px;
    margin-top: 20px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 🟢 HOME PAGE
# =====================================================

if st.session_state.page == "home":

    st.markdown("""
    <div style="text-align:center; margin-top:120px;">
        <h1>🌤 Weather Intelligence</h1>
        <p style="color:gray;">Real-time weather dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    city = st.text_input("📍 Enter City", placeholder="e.g. Bangalore")

    if st.button("🚀 Get Weather"):
        if city:
            with st.spinner("Fetching weather data... ⏳"):
                time.sleep(1.5)

            st.session_state.location = city
            add_to_recent(city)
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.warning("Please enter a city")

    # 📍 Recent Searches
    if st.session_state.recent:
        st.markdown("### 🔍 Recent Searches")

        cols = st.columns(len(st.session_state.recent))
        for i, c in enumerate(st.session_state.recent):
            if cols[i].button(c):
                st.session_state.location = c
                st.session_state.page = "dashboard"
                st.rerun()

# =====================================================
# 🔵 DASHBOARD PAGE
# =====================================================

elif st.session_state.page == "dashboard":

    location = st.session_state.location

    # 🔙 Back Button
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("⬅"):
            st.session_state.page = "home"
            st.rerun()

    if not API_KEY:
        st.error("❌ API key missing")
        st.stop()

    with st.spinner("Loading dashboard... ⏳"):
        time.sleep(1)

    df, current = get_weather_data(location)

    if df.empty:
        st.error("❌ Invalid city or API issue")
        st.stop()

    temp = current['main']['temp']
    feels = current['main']['feels_like']
    weather = current['weather'][0]['description']
    humidity = current['main']['humidity']
    wind = current['wind']['speed']

    icon = current['weather'][0]['icon']
    icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"

    # 🌟 HERO
    st.markdown(f"""
    <div class="hero">
        <img src="{icon_url}" width="100">
        <div class="hero-temp">{temp:.1f}°C</div>
        <div class="hero-desc">{weather.title()} in {location.title()}</div>
    </div>
    """, unsafe_allow_html=True)

    # 📊 CARDS
    col1, col2, col3, col4 = st.columns(4)

    def card(title, value):
        return f"<div class='card'><h4>{title}</h4><h2>{value}</h2></div>"

    col1.markdown(card("Feels Like", f"{feels:.1f}°C"), unsafe_allow_html=True)
    col2.markdown(card("Humidity", f"{humidity}%"), unsafe_allow_html=True)
    col3.markdown(card("Wind", f"{wind} m/s"), unsafe_allow_html=True)
    col4.markdown(card("Rain (Total)", f"{df['Rain'].sum():.1f} mm"), unsafe_allow_html=True)

    st.markdown("---")

    # 📅 Forecast
    st.markdown("<div class='section'>📅 5-Day Forecast</div>", unsafe_allow_html=True)

    for i in range(0, len(df), 8):
        day = df.iloc[i:i+8]

        date = day['Datetime'].iloc[0]
        day_name = date.strftime("%a").upper()
        date_str = date.strftime("%m/%d")

        max_temp = day['Temp'].max()
        min_temp = day['Temp'].min()

        weather_day = day['Weather'].mode()[0]
        rain = day['Rain'].sum()

        icon_day = day['Icon'].iloc[0]
        icon_url_day = f"https://openweathermap.org/img/wn/{icon_day}@2x.png"

        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 3, 1])

        with col1:
            st.markdown(f"**{day_name}**")
            st.caption(date_str)

        with col2:
            st.image(icon_url_day, width=50)

        with col3:
            st.markdown(f"### {max_temp:.0f}° / {min_temp:.0f}°")

        with col4:
            st.markdown(weather_day.title())

        with col5:
            st.markdown(f"💧 {rain:.0f} mm")

        st.divider()

    # 📈 Chart
    st.markdown("<div class='section'>📈 Temperature Trend</div>", unsafe_allow_html=True)
    fig = px.line(df, x="Datetime", y="Temp", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # 📥 Download
    st.download_button(
        "⬇ Download Excel",
        convert_to_excel(df),
        "weather.xlsx"
    )
