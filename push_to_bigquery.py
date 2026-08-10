import duckdb
from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID

DB_PATH = "daily_meteorology.duckdb"

GOLD_TABLES = [
    "gold_city_daily",
]

def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    client.create_dataset(dataset_ref, exists_ok=True)

    for table in GOLD_TABLES:
        print(f"Pushing {table}...")
        df = con.sql(f"SELECT * FROM {table}").df()

        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(
            df, f"{dataset_ref}.{table}", job_config=job_config
        )
        job.result()  # block until the load finishes
        print(f"  loaded {job.output_rows} rows")

    con.close()
    print("Done.")

if __name__ == "__main__":
    main()