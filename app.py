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
        return requests.get("http://ip-api.com/json/").json()['city']
    except:
        return "Bangalore"

# 🌦 Weather Data
def get_weather_data(location):
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()

        if data.get("cod") != "200":
            return pd.DataFrame()

        rows = []
        for e in data['list']:
            rows.append({
                "Datetime": e['dt_txt'],
                "Temp": e['main']['temp'],
                "Humidity": e['main']['humidity'],
                "Rain": e.get('rain', {}).get('3h', 0),
                "Weather": e['weather'][0]['description']
            })

        df = pd.DataFrame(rows)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        return df
    except:
        return pd.DataFrame()

# 📅 Summary
def daily_summary(df):
    df['Date'] = df['Datetime'].dt.date
    s = df.groupby('Date').agg({
        'Temp':['min','max','mean'],
        'Rain':'sum'
    })
    s.columns = ['Min Temp','Max Temp','Avg Temp','Total Rain']
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

# 🎨 THEME (🔥 temperature intensity)
def get_theme(desc, temp, hour):
    desc = desc.lower()
    is_night = hour >= 18 or hour <= 6

    intensity = min(max((temp - 15)/25, 0), 1)

    if "rain" in desc:
        c1, c2 = "#00c6ff", "#0072ff"
    elif "cloud" in desc:
        c1, c2 = "#757f9a", "#d7dde8"
    elif "clear" in desc:
        c1, c2 = "#f7971e", "#ffd200"
    else:
        c1, c2 = "#4facfe", "#00f2fe"

    if is_night:
        c1, c2 = "#141E30", "#243B55"

    opacity = 0.15 + intensity * 0.3
    card = f"rgba(255,255,255,{opacity})"

    return f"{c1}, {c2}", card

# 🎥 Lottie
def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def get_anim(desc):
    desc = desc.lower()
    if "rain" in desc:
        return load_lottie("https://assets2.lottiefiles.com/packages/lf20_jmBauI.json")
    if "cloud" in desc:
        return load_lottie("https://assets2.lottiefiles.com/packages/lf20_KUFdS6.json")
    return load_lottie("https://assets2.lottiefiles.com/packages/lf20_Stt1Rk.json")

# 🔊 Sound
def get_sound(desc):
    desc = desc.lower()
    if "rain" in desc:
        return "https://www.soundjay.com/nature/rain-01.mp3"
    if "wind" in desc:
        return "https://www.soundjay.com/nature/wind-01.mp3"
    return None

# ================= UI =================

loc = get_location()

st.sidebar.title("⚙ Control Panel")
location = st.sidebar.text_input("📍 City", loc)
view = st.sidebar.radio("📊 View", ["Overview","Trends","Raw Data"])

# ================= MAIN =================

if st.sidebar.button("Get Weather"):

    df = get_weather_data(location)
    if df.empty:
        st.error("Invalid city/API issue")
        st.stop()

    summary = daily_summary(df)

    temp = df['Temp'].iloc[0]
    weather = df['Weather'].iloc[0]
    emoji = get_emoji(weather)

    hour = pd.Timestamp.now().hour
    gradient, card_color = get_theme(weather, temp, hour)

    # 🌈 Animated Background
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(270deg, {gradient});
        background-size: 400% 400%;
        animation: bgMove 12s ease infinite;
    }}
    @keyframes bgMove {{
        0%{{background-position:0%}}
        50%{{background-position:100%}}
        100%{{background-position:0%}}
    }}
    </style>
    """, unsafe_allow_html=True)

    # 🔥 Title Fix
    st.markdown(f"""
    <h1 style='text-align:center;color:white;
    text-shadow:2px 2px 10px black;'>
    {emoji} {location} | {temp:.1f}°C — {weather.title()}
    </h1>
    """, unsafe_allow_html=True)

    # 🎥 Animation (fixed)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st_lottie(get_anim(weather), height=120)

    # 🔊 Sound
    sound = get_sound(weather)
    if sound:
        st.markdown(f"""
        <audio autoplay loop>
        <source src="{sound}" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)

    # 🧊 Cards
    cols = st.columns(4)

    def card(t,v):
        return f"""
        <div style="background:{card_color};
        padding:20px;border-radius:15px;
        backdrop-filter:blur(10px);
        text-align:center;">
        <h4>{t}</h4><h2>{v}</h2></div>
        """

    cols[0].markdown(card("Avg Temp",f"{df['Temp'].mean():.1f}°C"),True)
    cols[1].markdown(card("Max Temp",f"{df['Temp'].max():.1f}°C"),True)
    cols[2].markdown(card("Min Temp",f"{df['Temp'].min():.1f}°C"),True)
    cols[3].markdown(card("Rain",f"{df['Rain'].sum():.1f} mm"),True)

    # 📊 Views
    if view=="Overview":
        st.dataframe(summary)
    elif view=="Trends":
        st.plotly_chart(px.line(df,x="Datetime",y="Temp",markers=True))
    else:
        st.dataframe(df)

    # 📥 Download
    st.download_button("Download Excel",convert_to_excel(summary),"weather.xlsx")
