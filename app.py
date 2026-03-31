import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

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

# 🎨 Clean Dark Theme
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}

/* Title */
.title {
    text-align: center;
    font-size: 40px;
    font-weight: 700;
    margin-bottom: 20px;
}

/* Cards */
.card {
    background: #1c2333;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

/* Table */
[data-testid="stDataFrame"] {
    background: #111827;
    border-radius: 10px;
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

    df = get_weather_data(location)

    if df.empty:
        st.error("Invalid city or API issue")
        st.stop()

    summary = daily_summary(df)

    temp = df['Temp'].iloc[0]
    weather = df['Weather'].iloc[0]
    emoji = get_emoji(weather)

    # 🌟 Title
    st.markdown(f"""
    <div class="title">
    {emoji} {location.title()} | {temp:.1f}°C — {weather.title()}
    </div>
    """, unsafe_allow_html=True)

    # 📊 Cards
    col1, col2, col3, col4 = st.columns(4)

    def card(t, v):
        return f"""
        <div class="card">
            <h4 style="color:#9ca3af;">{t}</h4>
            <h2>{v}</h2>
        </div>
        """

    col1.markdown(card("Avg Temp", f"{df['Temp'].mean():.1f}°C"), True)
    col2.markdown(card("Max Temp", f"{df['Temp'].max():.1f}°C"), True)
    col3.markdown(card("Min Temp", f"{df['Temp'].min():.1f}°C"), True)
    col4.markdown(card("Rain", f"{df['Rain'].sum():.1f} mm"), True)

    st.markdown("---")

    # 📊 Views
    if view == "Overview":
        st.dataframe(summary, use_container_width=True)

    elif view == "Trends":
        fig = px.line(df, x="Datetime", y="Temp", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.dataframe(df, use_container_width=True)

    # 📥 Download
    st.download_button(
        "⬇ Download Excel",
        convert_to_excel(summary),
        "weather.xlsx"
    )
