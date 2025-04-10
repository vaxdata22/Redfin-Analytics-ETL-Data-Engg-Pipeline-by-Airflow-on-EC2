
# Import necessary libraries and modules
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd


# Define S3 bucket names for the Redfin data
LANDING_ZONE_BUCKET = 'redfin-analytics-landing-zone-raw-data'
TRANSFORMED_DATA_BUCKET = 'redfin-analytics-transformed-data-bucket'


# # Source data URL link from - https://www.redfin.com/news/data-center/
HOUSING_BY_CITY_URL = 'https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz'


# Function to extract and dump raw data into S3 while returning a DataFrame object
def extract_dump_data(ti):
    # Read data from Redfin URL
    df = pd.read_csv(HOUSING_BY_CITY_URL, compression='gzip', sep='\t')

    # Report the size of the transformed dataset
    print('Num of rows:', len(df))
    print('Num of cols:', len(df.columns))

    # Generate unique filename with timestamp
    filename = f"redfin_data_{datetime.now().strftime('%d%m%Y%H%M%S')}.csv"

    # Convert DataFrame to CSV string (raw data)and save locally
    local_path = f"/tmp/{filename}"
    df.to_csv(local_path, index=False)

    # Upload raw CSV from Local Path to the landing zone bucket
    s3 = S3Hook(aws_conn_id='aws_new_conn')
    s3.load_file(
        filename=local_path,
        key=filename,
        bucket_name=LANDING_ZONE_BUCKET,
        replace=True
    )

    # Push Local Path and filename information to XCom using `ti`
    ti.xcom_push(key='filename', value=filename)
    ti.xcom_push(key='local_path', value=local_path)


# Function to transform and load cleaned data into the second S3 bucket
def transform_load_data(ti):
    # Pull filename and Local Path information from XCom using `ti`
    filename = ti.xcom_pull(task_ids='extract_redfin_data_and_dump_copy_in_first_bucket', key='filename')
    local_path = ti.xcom_pull(task_ids='extract_redfin_data_and_dump_copy_in_first_bucket', key='local_path')

    df = pd.read_csv(local_path)

    # Data cleaning 1: Remove commas from the 'city' column
    df['city'] = df['city'].str.replace(',', '', regex=True)

    # Data cleaning 2: First select 24 fields from the raw dataset
    selected_cols = [
        'period_begin', 'period_end', 'period_duration', 'region_type', 'region_type_id', 'table_id',
        'is_seasonally_adjusted', 'city', 'state', 'state_code', 'property_type', 'property_type_id',
        'median_sale_price', 'median_list_price', 'median_ppsf', 'median_list_ppsf', 'homes_sold',
        'inventory', 'months_of_supply', 'median_dom', 'avg_sale_to_list', 'sold_above_list',
        'parent_metro_region_metro_code', 'last_updated'
    ]

    # Data cleaning 3: Drop all records that have null values
    df = df[selected_cols].dropna()

    # Data cleaning 4: Typecast the 'period_begin' and 'period_end' from object to datetime datatype
    df['period_begin'] = pd.to_datetime(df['period_begin'])
    df['period_end'] = pd.to_datetime(df['period_end'])

    # Data cleaning 5: Extract year data from 'period_begin_in_years' and 'period_end_in_years' into 2 new columns
    df["period_begin_in_years"] = df['period_begin'].dt.year
    df["period_end_in_years"] = df['period_end'].dt.year

    # Data cleaning 6: Extract month name data from 'period_begin_in_months' and 'period_end_in_months' into 2 new columns
    df["period_begin_in_months"] = df['period_begin'].dt.strftime('%B')  # Convert to month name
    df["period_end_in_months"] = df['period_end'].dt.strftime('%B')      # Convert to month name

    # Report the size of the transformed dataset
    print('Num of rows:', len(df))
    print('Num of cols:', len(df.columns))

    # Save transformed file to temp
    transformed_path = f"/tmp/cleaned_{filename}"
    df.to_csv(transformed_path, index=False)

    # Upload to transformed bucket
    s3 = S3Hook(aws_conn_id='aws_new_conn')
    s3.load_file(
        filename=transformed_path,
        key=f"cleaned_{filename}",
        bucket_name=TRANSFORMED_DATA_BUCKET,
        replace=True
    )

    # Optional: Clean up temp files
    os.remove(local_path)
    os.remove(transformed_path)


# Specify essential arguments for parameters
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 4, 4),
    'email': ['donatus.enebuse@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=4)
}


# Authoring the ETL orchestration DAG along with necessary arguments
with DAG('redfin_analytics_etl_dag',
    default_args=default_args,
    description='ETL pipeline for Redfin housing market data', 
    schedule_interval = '@monthly',
    catchup=False) as dag:
    
    # Extract source data and dump a copy in the raw data bucket
    extract_dump_redfin_data = PythonOperator(
    task_id= 'extract_redfin_data_and_dump_copy_in_first_bucket',
    python_callable=extract_dump_data
    )

    # Transform the raw data and load to transformed data bucket
    transform_load_redfin_data = PythonOperator(
    task_id= 'transform_redfin_data_and_load_into_second_bucket',
    python_callable=transform_load_data
    )

    # Define the tasks sequence       
    extract_dump_redfin_data >> transform_load_redfin_data
