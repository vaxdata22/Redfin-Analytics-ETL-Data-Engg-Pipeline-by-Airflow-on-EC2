# Redfin Analytics end-to-end ETL data pipeline by Airflow on an EC2 instance
This is an end-to-end AWS Cloud ETL project. This data pipeline orchestration uses Apache Airflow on AWS EC2 as well as Snowpipe. 
It demonstrates how to build ETL data pipeline that would perform data transformation using Python on Apache Airflow as well as automatic data ingestion into a Snowflake data warehouse via Snowpipe. 
The data would then be visualized using Microsoft Power BI.
<br><br>

![img1](screenshots/img1.png)
<br><br>

## GENERAL OVERVIEW OF PROJECT
This is a Redfin Real Estate Data Analytics Python ETL data engineering project using Apache Airflow, Snowpipe, Snowflake and AWS services.
This project shows how to connect to the Redfin data source to extract real estate data using Python and dump the raw data into an Amazon S3 bucket, then transform the raw data using Pandas and load it into another Amazon S3 bucket. 

As soon as the transformed data lands inside the second S3 bucket, Snowpipe would be triggered this would automatically run a `COPY` command to load the transformed data into a Snowflake data warehouse table. Power BI would be connected to the snowflake data warehouse to then visualize the data to obtain insights.

Apache airflow would be used to orchestrate and automate this process.

Apache Airflow is an open-source platform used for orchestrating and scheduling workflows of tasks and data pipelines. Apache Airflow would be installed on an EC2 instance to orchestrate the pipeline.

The project was inspired by Dr Yemi Olanipekun, whose tutorials benefitted me a lot.
<br><br>

## PROJECT REQUIREMENTS
1. Fundamental knowledge of SQL, Python, CSV/JSON, AWS Cloud, Apache Airflow, DW & ETL concepts

2. Familiarity with fundamentals Snowflake DW and S3-Snowpipe data auto-ingestion concepts like SQS Queue
  
3. Redfin real estate City houses dataset (to serve as the source of the real estate data)
  
4. AWS EC2 instance with at least 20 GB storage (t3.xlarge) Ubuntu; and AWS S3 bucket as Data Lake
  
5. Code Editor (I used VSCode) for connecting to EC2 instance to create code (DAG file) on Airflow
  
6. Apache Airflow for orchestration (authoring of the ETL workflow via DAG) & services connections
  
7. Good knowledge and skills in data analytics and visualization on Microsoft Power BI tool
  
8. Perseverance to troubleshoot and resolve errors and failures, read logs, rebuild components, etc
<br><br>

## STEPS OF THE WORKFLOW
The following account of the project development process may not be enough to enable the reader code along or replicate the whole process from start to finish. 
For instance, there is no detailing of the steps involved in creating account with Amazon AWS. 
There is also no detailing of the steps in creating an IAM User whose credentials would be used by Airflow, setting up the S3 buckets, deploying the Snowpipe along with SQS Queue configuration on the S3 bucket, setting up Snowflake data warehouse and connecting Power BI to it, spinning up the AWS EC2 instance from scratch and preparing it to work with Airflow (Firewall settings for HTTP/HTTPS/SSH and attaching the IAM Role), connecting VSCode to the EC2 instance, as well as accessing Airflow via web browser.

However a person who is knowledgeable in Data Engineering skills should be familiar with how these are set up. 
By the way the reader who is not knowledgeable in these areas is hereby encouraged to do their own research, enroll in a Data Engineering bootcamp or learn from data engineering tutorials available online on some websites or some great channels on YouTube  (such as Tuple Spectra), or reach out to me for clarification. 
With that out of the way, let’s go over the key steps in this project.

Having satisfied all the 8 requirements in the preceding section, I proceeded to carry out the following setup:
<br><br>

### STEP 1: Examining the source data and preliminary coding:
The source data is a real estate data obtained from https://www.redfin.com/news/data-center/.

The particular dataset of interest is the US Housing Market data by `City`, obtained from the following link: 

https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz

The data is in a compressed format (GZ).

The first part of the development process was done in an online Python Notebook environment (Google Colab, colab.google) in order to examine the source data to see the fields and records. 
This would also serve as a means to code out the data transform function and other preliminary code.

![img2](screenshots/img2.png)
<br><br>

The source dataset originally comprises of 5779946 records and 58 fields.

The data transformation included the following activities:

First, the following 24 columns were selected to be of interest:
```
period_begin,
period_end,
period_duration,
region_type,
region_type_id,
table_id,
is_seasonally_adjusted, 
city, 
state, 
state_code, 
property_type, 
property_type_id,
median_sale_price, 
median_list_price, 
median_ppsf, 
median_list_ppsf, 
homes_sold,
inventory, 
months_of_supply, 
median_dom, 
avg_sale_to_list, 
sold_above_list, 
parent_metro_region_metro_code, 
last_updated
```

Next, as part of data cleaning, these actions were taken on the resulting dataset:
•	Drop all records that have null values. 

•	Typecast the `period_begin` and `period_end` to DATETIME datatype. 

•	Extract year data from `period_begin_in_years` and `period_end_in_years` into 2 new columns.

•	Extract month data from `period_begin_in_months` and `period_end_in_months` into 2 new columns. 

•	Map the month number to their respective month name.

![img3](screenshots/img3.png)
<br><br>

![img4](screenshots/img4.png)
<br><br>

The transformed dataset was the reported to be 4500063 records and 28 fields. 

See the Proof-of-Concept (PoC) Python Notebook file [here](codes/Redfin_Analytics_data_transform_PoC.ipynb). 
<br><br>

### STEP 2: Created the necessary S3 buckets:
* Landing zone bucket: `redfin-analytics-landing-zone-raw-data`
  
* Transformed data bucket: `redfin-analytics-transformed-data-bucket`
  
![img5](screenshots/img5.png)
<br><br>

![img6](screenshots/img6.png)
<br><br>

### STEP 3: Prepared the Snowflake data warehouse environment:
Based on the 28 selected columns for the transformed dataset, the destination table schema was designed using the appropriate data type.
The data warehouse, destination table, staging area, and Snowpipe were then created using a prepared SQL script. 

See the SQL file [here](codes/redfin_analytics_snowflake_dw_create.sql).

![img7](screenshots/img7.png)
<br><br>

Verified the table schema:

`DESC TABLE redfin_analytics_database.redfin_analytics_schema.redfin_analytics_table;`

![img8](screenshots/img8.png)
<br><br>

Checked the properties of the pipe created:

`DESC PIPE redfin_analytics_database.snowpipe_schema.redfin_analytics_snowpipe;`

![img9](screenshots/img9.png)
<br><br>

Took note of the `Notification Channel ARN` string.
<br><br>

### STEP 4: S3 bucket configuration for Snowpipe:
First tested the external stage created on Snowflake by uploading a test CSV file to the `redfin-analytics-transformed-data-bucket S3 bucket`. 

See the test file [here](test_data/test_stage_pipe.csv).

![img10](screenshots/img10.png)
<br><br>

![img11](screenshots/img11.png)
<br><br>

Then this was tested by running the following command on the Snowflake SQL Workspace:

`list @redfin_analytics_database.external_stage_schema.redfin_dw_ext_stage;`

![img12](screenshots/img12.png)
<br><br>

Next, configured the S3 bucket to make it trigger Snowpipe. This was done by creating an Event Notification on the S3 bucket via the bucket `Properties` settings:
* Event name: `redfin-analytics-snowpipe-event`

* Object creation: `All object create events`
  
* Destination: `SQS Queue`
  
* Specfy SQS Queue (Enter SQS Queue ARN): <<Entered the `Notification Channel ARN` of Snowpipe>>
  
![img13](screenshots/img13.png)
<br><br>

Checked the destination table in Snowflake to see if Snowpipe is working:
```
SELECT *
FROM redfin_analytics_database.redfin_analytics_schema.redfin_analytics_table 
LIMIT 10;
```

![img14](screenshots/img14.png)
<br><br>

```
SELECT COUNT(*) AS Number_Of_Records
FROM redfin_analytics_database.redfin_analytics_schema.redfin_analytics_table;
```

![img15](screenshots/img15.png)
<br><br>

In preparation for the rest of the project, the S3 bucket was emptied and the Snowflake table re-created:

![img16](screenshots/img16.png)
<br><br>

![img17](screenshots/img17.png)	
<br><br>

### STEP 5: Provisioning the EC2 instance:
* Instance name: `redfin-analytics-etl-pipeline-computer`

* Instance type: t3.xlarge, 20 GiB storage (instead of the default 8 GiB)

* EC2 role name: `ec2-access-to-s3-role`
  
** Details: AWS Service, Use case is EC2

** Permissions: `AmazonS3FullAccess`

![img18](screenshots/img18.png)
<br><br>

These required dependencies were then installed on EC2 for this project:

#### Update package list
```
sudo apt update
```
#### Installed the Python environment
```
sudo apt install python3-pip
```
#### Checked the version of Python installed
```
python3 –version
```
#### Installed a Python virtual environment package
```
sudo apt install python3.12-venv
```
#### Install necessary packages that would enable smooth installation of airflow-providers-amazon
```
sudo apt install -y libxml2-dev libxmlsec1-dev libxmlsec1-openssl pkg-config
```
#### Created the virtual environment
```
python3.12 -m venv redfin_analytics_etl_venv
```
#### Activated the virtual environment
```
source redfin_analytics_etl_venv/bin/activate
```
#### Installed Pandas
```
pip install pandas
```
#### Installed Apache Airflow
```
pip install apache-airflow
```
#### Installed Apache Airflow Providers for Amazon
```
pip install apache-airflow-providers-amazon
```
#### To run Airflow in dev mode
```
airflow standalone
```
<br><br>

The DAG was written to orchestrate the workflow once every month. 

See the finished DAG file [here](codes/redfin_analytics_etl_dag.py).

![img19](screenshots/img19.png)
<br><br>
	
This orchestration made use of a necessary AWS Airflow connection which was added via the Airflow GUI:
* Connection ID: `aws_new_conn`

* Connection Type: Amazon Web Services

* AWS Access Key: <<THE IAM USER ACCESS KEY>>

* AWS Secret Access Key: <<THE IAM USER SECRET ACCESS KEY>>

* Extra:
        ```
        {
           "region_name": "af-south-1"
        }
        ```
<br><br>

The DAG tasks ready to be triggered:

![img20](screenshots/img20.png)
<br><br>

### STEP 6: Preparation before testing the orchestration, and triggering the DAG:
The state of the S3 buckets and the Snowflake table before triggering the DAG.

![img21](screenshots/img21.png)
<br><br>

![img22](screenshots/img22.png)
<br><br>

![img23](screenshots/img23.png)
<br><br>

After triggering the DAG:

The first task was a success and it took about 10 minutes to complete.

![img24](screenshots/img24.png)
<br><br>

![img25](screenshots/img25.png)
<br><br>

The second task was also a success and it took a little more than 4 minutes to complete.

![img26](screenshots/img26.png)
<br><br>

![img27](screenshots/img27.png)
<br><br>

The buckets were then observed to contain data:

![img28](screenshots/img28.png)
<br><br>

![img29](screenshots/img29.png)
<br><br>

The Snowflake data warehouse table was also seen to contain the 4.5 million records data.

![img30](screenshots/img30.png)
<br><br>

![img31](screenshots/img31.png)
<br><br>

This confirms that the entire orchestration was indeed successful.

![img32](screenshots/img32.png)
<br><br>

![img33](screenshots/img33.png)
<br><br>

![img34](screenshots/img34.png)
<br><br>

![img35](screenshots/img35.png)
<br><br>

### STEP 7: Connecting Power BI to Snowflake:
* Server: `xxxxxxx-xxxxxxx.snowflakecomputing.com`

* Warehouse: `redfin_analytics_warehouse`

* Username: <<MY SNOWFLAKE ACCOUNT USERNAME>>

* Password: <<MY SNOWFLAKE ACCOUNT PASSWORD>>
  
![img36](screenshots/img36.png)
<br><br>

Loaded the data via `DirectQuery`.

![img37](screenshots/img37.png)
<br><br>

![img38](screenshots/img38.png)
<br><br>

The visualization dashboard.

![img39](screenshots/img39.png)
<br><br>

## CHALLENGES AND FINAL THOUGHTS
I did not encounter any real challenges in this project. The orchestration was quite straightforward and building it was really enjoyable.

I am thankful to Dr. Opeyemi ‘Yemi’ Olanipekun for inspiring me to carry out this project. His passionate way of teaching and guidance is second to none.
<br><br>

## RESOURCES TO LOOK THROUGH
https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro

https://docs.snowflake.com/en/sql-reference/sql/create-file-format

https://docs.snowflake.com/en/sql-reference/sql/create-stage

https://docs.snowflake.com/en/sql-reference/sql/copy-into-table

https://docs.snowflake.com/en/sql-reference/sql/create-pipe

https://docs.snowflake.com/en/sql-reference/sql/desc-table

https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/emr/emr.html

https://registry.astronomer.io/providers/amazon/versions/latest/modules/emrjobflowsensor

https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-commandrunner.html

https://registry.astronomer.io/providers/amazon/versions/latest/modules/emraddstepsoperator

https://registry.astronomer.io/providers/apache-airflow-providers-amazon/versions/8.4.0/modules/EmrStepSensor
<br><br>

Cover Image credited to Tuple Spectra channel on Youtube.

### Thank you for going through this project with me!


