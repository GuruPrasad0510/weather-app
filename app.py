import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="Weather Intelligence Pro", layout="wide")

# 🌍 Auto location
def get_location():
    try:
        return requests.get("http://ip-api.com/json/", timeout=5).json().get('city', 'Bangalore')
    except:
        return "Bangalore"

# 🌦 Weather Data
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
                "Feels Like": e['main']['feels_like'],
                "Humidity": e['main']['humidity'],
                "Pressure": e['main']['pressure'],
                "Wind": e['wind']['speed'],
                "Rain": e.get('rain', {}).get('3h', 0),
                "Weather": e['weather'][0]['description']
            })

        df = pd.DataFrame(rows)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        return df, data['list'][0]

    except:
        return pd.DataFrame(), None

# 📅 Summary
def daily_summary(df):
    df['Date'] = df['Datetime'].dt.date
    s = df.groupby('Date').agg({
        'Temp': ['min', 'max', 'mean'],
        'Rain': 'sum'
    })
    s.columns = ['Min Temp', 'Max Temp', 'Avg Temp', 'Total Rain']
    return s.reset_index()

# 📥 Excel
def convert_to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf

# 🌤 Emoji
def get_emoji(desc):
    desc = desc.lower()
    if "rain" in desc: return "🌧"
    if "cloud" in desc: return "☁"
    if "clear" in desc: return "☀"
    return "🌤"

# ================= UI =================

st.markdown("""
<style>
.stApp { background-color: #0e1117; color: white; }
.title { text-align: center; font-size: 42px; font-weight: 700; }
.card {
    background: #1c2333;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
loc = get_location()
st.sidebar.title("⚙ Control Panel")
location = st.sidebar.text_input("📍 City", loc)
view = st.sidebar.radio("📊 View", ["Overview", "Trends", "Raw Data"])

# ================= MAIN =================

if st.sidebar.button("Get Weather"):

    df, current = get_weather_data(location)

    if df.empty:
        st.error("❌ Invalid city or API issue")
        st.stop()

    summary = daily_summary(df)

    # 🌟 HEADER
    temp = current['main']['temp']
    weather = current['weather'][0]['description']
    emoji = get_emoji(weather)

    st.markdown(f"""
    <div class="title">
    {emoji} {location.title()} — {temp:.1f}°C | {weather.title()}
    </div>
    """, unsafe_allow_html=True)

    # 📊 ACCUWEATHER STYLE CARDS
    col1, col2, col3, col4 = st.columns(4)

    def card(title, value):
        return f"<div class='card'><h4>{title}</h4><h2>{value}</h2></div>"

    col1.markdown(card("Feels Like", f"{current['main']['feels_like']}°C"), True)
    col2.markdown(card("Humidity", f"{current['main']['humidity']}%"), True)
    col3.markdown(card("Wind", f"{current['wind']['speed']} m/s"), True)
    col4.markdown(card("Pressure", f"{current['main']['pressure']} hPa"), True)

    st.markdown("---")

    # 📊 VIEWS
    if view == "Overview":
        st.subheader("📅 Daily Summary")
        st.dataframe(summary, use_container_width=True)

    elif view == "Trends":
        st.subheader("📈 Temperature Trend")
        fig = px.line(df, x="Datetime", y="Temp", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.subheader("📋 Raw Data")
        st.dataframe(df, use_container_width=True)

    # 📥 Download
    st.download_button(
        "⬇ Download Excel",
        convert_to_excel(summary),
        "weather.xlsx"
    )
