# Daily Meteorology

A daily-refreshing data pipeline tracking weather and air quality across 8 cities
(4 Malaysian, 4 global), built to practice true incremental scheduling — not just
a one-off historical load.

## Live dashboard
[View on Streamlit Community Cloud](https://dailymeteorology-yksuxvbwu2avrezf72ztec.streamlit.app/)

## Architecture
- **Extract:** Open-Meteo API (archive endpoint for backfill, forecast endpoint for
  daily incremental pulls — avoids the reanalysis data lag on the archive API)
- **Bronze/Silver/Gold:** DuckDB + dbt, with air quality aggregated hourly → daily in silver
- **Orchestration:** Airflow, `@daily` schedule, idempotent daily load (delete + insert per city/date)
- **Warehouse:** BigQuery (gold layer only)
- **Dashboard:** Streamlit + Plotly, reading live from BigQuery, with a data-freshness check

## Local setup
1. `pip install -r requirements.txt`
2. Place your GCP service account key in `secrets/` (see `.gitignore`)
3. `docker compose up -d` to run Airflow
4. `streamlit run app.py` for the dashboard
