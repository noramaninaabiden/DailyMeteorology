import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from datetime import date
from google.oauth2 import service_account

st.set_page_config(page_title="Daily Meteorology", layout="wide")

PROJECT_ID = "daily-meteorology"
DATASET_ID = "daily_meteorology"
TABLE = f"{PROJECT_ID}.{DATASET_ID}.gold_city_daily"

@st.cache_resource
def get_bigquery_client():
    if "gcp_service_account" in st.secrets:
        # Running on Streamlit Cloud — credentials come from the secrets manager
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    else:
        # Running locally — uses GOOGLE_APPLICATION_CREDENTIALS env var
        return bigquery.Client(project=PROJECT_ID)

@st.cache_data(ttl=3600)
def load_data():
    client = get_bigquery_client()
    query = f"SELECT * FROM `{TABLE}` ORDER BY date"
    return client.query(query).to_dataframe()

df = load_data()
df["date"] = pd.to_datetime(df["date"]).dt.date

st.title("🌦️ Daily Meteorology Dashboard")

# --- Freshness check ---
latest_date = df["date"].max()
days_stale = (date.today() - latest_date).days
if days_stale > 1:
    st.warning(f"Data is {days_stale} days old — latest date is {latest_date}. Check the Airflow DAG.")
else:
    st.caption(f"Data current as of {latest_date}")

# --- City filter ---
cities = sorted(df["city"].unique())
selected_cities = st.multiselect("Cities", cities, default=cities)

filtered = df[df["city"].isin(selected_cities)]

# --- Today's snapshot ---
st.subheader("Latest readings")
snapshot = filtered[filtered["date"] == latest_date][
    ["city", "temp_max_c", "temp_min_c", "precipitation_mm", "avg_us_aqi"]
]
st.dataframe(snapshot, use_container_width=True)

# --- Temperature trend ---
st.subheader("Temperature trend")
fig_temp = px.line(
    filtered, x="date", y="temp_max_c", color="city",
    labels={"temp_max_c": "Max Temp (°C)", "date": "Date"},
)
st.plotly_chart(fig_temp, use_container_width=True)

# --- Air quality trend ---
st.subheader("Air quality (US AQI) trend")
fig_aqi = px.line(
    filtered, x="date", y="avg_us_aqi", color="city",
    labels={"avg_us_aqi": "Avg US AQI", "date": "Date"},
)
st.plotly_chart(fig_aqi, use_container_width=True)

# --- Precipitation ---
st.subheader("Precipitation")
fig_precip = px.bar(
    filtered, x="date", y="precipitation_mm", color="city",
    labels={"precipitation_mm": "Precipitation (mm)", "date": "Date"},
)
st.plotly_chart(fig_precip, use_container_width=True)