import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="Weather Intelligence", layout="wide")

# ------------------ FUNCTIONS ------------------

def get_location():
    try:
        return requests.get("http://ip-api.com/json/", timeout=5).json()['city']
    except:
        return "Bangalore"


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
                "Weather": e['weather'][0]['description']
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


def get_emoji(desc):
    desc = desc.lower()
    if "rain" in desc: return "🌧"
    if "cloud" in desc: return "☁"
    if "clear" in desc: return "☀"
    return "🌤"


# ------------------ UI STYLE ------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0b1d3a, #111827);
    color: white;
}

/* HERO */
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

/* CARDS */
.card {
    background: #1e293b;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}

/* SECTION */
.section {
    font-size: 22px;
    margin-top: 20px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------

loc = get_location()

st.sidebar.title("⚙ Settings")
location = st.sidebar.text_input("📍 City", loc)
view = st.sidebar.radio("View", ["Overview", "Trends", "Raw Data"])

# ------------------ MAIN ------------------

if st.sidebar.button("Get Weather"):

    if not API_KEY:
        st.error("❌ API key missing")
        st.stop()

    df, current = get_weather_data(location)

    if df.empty:
        st.error("Invalid city or API issue")
        st.stop()

    temp = current['main']['temp']
    feels = current['main']['feels_like']
    weather = current['weather'][0]['description']
    humidity = current['main']['humidity']
    wind = current['wind']['speed']
    emoji = get_emoji(weather)

    # 🌟 HERO
    st.markdown(f"""
    <div class="hero">
        <div class="hero-temp">{emoji} {temp:.1f}°C</div>
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

    # ------------------ OVERVIEW (ACCUWEATHER STYLE) ------------------

    if view == "Overview":
        st.markdown("<div class='section'>📅 5-Day Forecast</div>", unsafe_allow_html=True)

        for i in range(0, len(df), 8):
            day = df.iloc[i:i+8]

            date = day['Datetime'].iloc[0]
            day_name = date.strftime("%a").upper()
            date_str = date.strftime("%m/%d")

            max_temp = day['Temp'].max()
            min_temp = day['Temp'].min()

            weather = day['Weather'].mode()[0]
            rain = day['Rain'].sum()

            emoji = get_emoji(weather)

            st.markdown(f"""
            <div style="
                background:#1e293b;
                padding:15px;
                border-radius:12px;
                margin-bottom:10px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <div>
                    <b>{day_name}</b><br>
                    <small>{date_str}</small>
                </div>

                <div style="font-size:22px;">
                    {emoji}
                </div>

                <div>
                    <b>{max_temp:.0f}°</b> / {min_temp:.0f}°
                </div>

                <div style="width:200px;">
                    {weather.title()}
                </div>

                <div>
                    💧 {rain:.0f} mm
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ------------------ TRENDS ------------------

    elif view == "Trends":
        st.markdown("<div class='section'>📈 Temperature Trend</div>", unsafe_allow_html=True)
        fig = px.line(df, x="Datetime", y="Temp", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # ------------------ RAW DATA ------------------

    else:
        st.markdown("<div class='section'>📋 Raw Data</div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)

    # 📥 DOWNLOAD
    st.download_button(
        "⬇ Download Excel",
        convert_to_excel(df),
        "weather.xlsx"
    )
