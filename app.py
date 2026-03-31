import requests
import datetime
import pandas as pd
import streamlit as st
from io import BytesIO
import os
API_KEY = os.getenv("b5b14b03e311269d6c45798efdf0f4bf")

def get_weather_data(location):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    weather_list = []

    for entry in data['list']:
        weather_list.append({
            "Datetime": entry['dt_txt'],
            "Temperature (°C)": entry['main']['temp'],
            "Feels Like (°C)": entry['main']['feels_like'],
            "Humidity (%)": entry['main']['humidity'],
            "Weather": entry['weather'][0]['description']
        })

    df = pd.DataFrame(weather_list)
    return df

# Streamlit UI
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