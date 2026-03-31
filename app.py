import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go


API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="Weather Intelligence", layout="wide")


def get_location():
    try:
        res = requests.get("http://ip-api.com/json/").json()
        return res['city']
    except:
        return "Bangalore"


def get_weather_data(location):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    if data.get("cod") != "200":
        st.error(f"Error: {data.get('message')}")
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


def get_city_coords(city):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    res = requests.get(url).json()
    if len(res) == 0:
        return None, None
    return res[0]['lat'], res[0]['lon']


st.markdown("<h1 style='text-align:center;'> Weather Intelligence Dashboard</h1>", unsafe_allow_html=True)


auto_location = get_location()

st.sidebar.title("⚙ Control Panel")
location = st.sidebar.text_input("City", auto_location)
view = st.sidebar.radio("View", ["Overview", "Trends", "Raw Data"])

multi_cities = st.sidebar.text_input(
    "Compare Cities",
    "Bangalore, Mumbai, Delhi"
)


if st.sidebar.button("Get Weather"):

    df, lat, lon = get_weather_data(location)

    if df.empty:
        st.stop()

    summary = daily_summary(df)

    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Temp", f"{df['Temp'].mean():.1f}°C")
    col2.metric("Max Temp", f"{df['Temp'].max():.1f}°C")
    col3.metric("Min Temp", f"{df['Temp'].min():.1f}°C")
    col4.metric("Rain", f"{df['Rain (mm)'].sum():.1f} mm")

    # =========================
    # LIVE RADAR
    # =========================
    st.markdown("### Live Rain Radar")

    tile_url = f"https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={API_KEY}"

    st.components.v1.html(f"""
        <div id="map" style="height: 500px;"></div>

        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

        <script>
            var map = L.map('map').setView([{lat}, {lon}], 6);

            L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

            L.tileLayer('{tile_url}', {{
                opacity: 0.6
            }}).addTo(map);
        </script>
    """, height=520)

    # =========================
    # MULTI CITY MAP
    # =========================
    st.markdown("### Multi-City Comparison")

    cities = [c.strip() for c in multi_cities.split(",")]
    map_data = []

    for city in cities:
        lat_c, lon_c = get_city_coords(city)
        if lat_c:
            temp = get_weather_data(city)[0]['Temp'].iloc[0]
            map_data.append({
                "City": city,
                "lat": lat_c,
                "lon": lon_c,
                "Temp": temp
            })

    multi_df = pd.DataFrame(map_data)

    if not multi_df.empty:
        fig = px.scatter_mapbox(
            multi_df,
            lat="lat",
            lon="lon",
            size="Temp",
            color="Temp",
            hover_name="City",
            zoom=3
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)

    # =========================
    #  AI ASSISTANT
    # =========================
    st.markdown("### AI Weather Assistant")

    user_question = st.text_input("Ask: Should I go out / workout?")

    def ai_response(df):
        avg_temp = df['Temp'].mean()
        rain = df['Rain (mm)'].sum()

        if rain > 5:
            return " Heavy rain expected. Avoid outdoor plans."
        elif avg_temp > 35:
            return " Too hot. Best to stay indoors or go out early morning."
        elif avg_temp < 20:
            return " Cool weather. Great for workouts!"
        else:
            return " Weather looks perfect for outdoor activities."

    if user_question:
        st.success(ai_response(df))

    # =========================
    # VIEWS
    # =========================
    if view == "Overview":
        st.dataframe(summary, use_container_width=True)

    elif view == "Trends":
        fig = px.line(df, x="Datetime", y="Temp", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    elif view == "Raw Data":
        st.dataframe(df, use_container_width=True)

    # DOWNLOAD
    excel = convert_to_excel(summary)

    st.download_button(
        "⬇ Download Excel",
        data=excel,
        file_name="weather_report.xlsx"
    )
