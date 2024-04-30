# Cyanobacteria Analysis with NASA CYAN Data

https://oceancolor.gsfc.nasa.gov/about/projects/cyan/

## Data Extraction from CYAN Project

Run the script below to extract L3B_CYAN_DAILY data for February 2 - 4, 2023. Save the data in .parquet format via path "./data/test.parquet".

```
python cyan_extract.py -datefrom 20230202 -dateto 20230204 -path test.parquet
```

## Data Analysis Dashboard

Run the script below to activate dashboard via sample data file "./data/L3B_CYAN_DAILY_mendota.parquet".

```
python dashboard.py -path data/L3B_CYAN_DAILY_mendota.parquet
```

## Cyanobacteria Forecasting

Run the script below to generate forecast via sample data file "./data/L3B_CYAN_DAILY_mendota.parquet".

```
python forecast.py -path data/L3B_CYAN_DAILY_mendota.parquet
```
