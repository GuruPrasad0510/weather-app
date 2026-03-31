import requests
import datetime
import pandas as pd
import streamlit as st
from io import BytesIO
import os
API_KEY = os.getenv("API_KEY")

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


st.title("Weather Forecast App")

location = st.text_input("Enter City Name:")

if st.button("Get Weather"):
    df = get_weather_data(location)

    st.subheader("Weather Data")
    st.dataframe(df)

    
    def convert_to_excel(df):
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return output

    excel_file = convert_to_excel(df)

    st.download_button(
        label="Download Excel",
        data=excel_file,
        file_name="weather_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
