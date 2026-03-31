import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px


API_KEY = os.getenv("API_KEY")

def get_location():
    try:
        res = requests.get("http://ip-api.com/json/").json()
        return res['city']
    except:
        return "Bangalore"


def get_weather_data(location):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    
    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message', 'Failed to fetch data')}")
        return pd.DataFrame()

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
    return df


def daily_summary(df):
    df['Date'] = df['Datetime'].dt.date
    summary = df.groupby('Date').agg({
        'Temp': ['min', 'max', 'mean'],
        'Rain (mm)': 'sum'
    })
    summary.columns = ['Min Temp', 'Max Temp', 'Avg Temp', 'Total Rain']
    return summary.reset_index()
    
def convert_to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output


st.set_page_config(page_title="Weather Dashboard", layout="wide")

st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
    margin-bottom: 20px;
    text-align: center;
}
.title {
    font-size: 42px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg, #4facfe, #00f2fe);
    -webkit-background-clip: text;
    color: transparent;
}
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="title">🌦 Weather Intelligence Dashboard</div>', unsafe_allow_html=True)


auto_location = get_location()

st.sidebar.title("⚙ Control Panel")
location = st.sidebar.text_input(" Enter City", auto_location)
view = st.sidebar.radio("Select View", ["Overview", "Trends", "Raw Data"])


if st.sidebar.button("Get Weather"):

    df = get_weather_data(location)

    if df.empty:
        st.stop()

    summary = daily_summary(df)

    
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f'<div class="card"> Avg Temp<br><h2>{df["Temp"].mean():.1f}°C</h2></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card"> Max Temp<br><h2>{df["Temp"].max():.1f}°C</h2></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="card"> Min Temp<br><h2>{df["Temp"].min():.1f}°C</h2></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="card"> Rain<br><h2>{df["Rain (mm)"].sum():.1f} mm</h2></div>', unsafe_allow_html=True)

    
    if view == "Overview":

        st.markdown("### Daily Summary")
        st.dataframe(summary, use_container_width=True)

        
        rain_total = df['Rain (mm)'].sum()

        if rain_total > 0:
            st.error(f" Rain Incoming! Total: {rain_total:.1f} mm")
        else:
            st.success(" Clear Weather Ahead")

    elif view == "Trends":

        st.markdown("###  Temperature Trends")

        fig = px.line(
            df,
            x="Datetime",
            y="Temp",
            markers=True
        )

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    elif view == "Raw Data":

        st.markdown("###  Forecast Data")
        st.dataframe(df, use_container_width=True)

    
    st.markdown("###  Export Report")

    excel = convert_to_excel(summary)

    st.download_button(
        "⬇ Download Excel",
        data=excel,
        file_name="weather_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
