# Cyanobacteria Analysis with NASA CYAN Data

## Data Extraction from CYAN Project

Example: Run code below to extract L3B_CYAN_DAILY data from February 2nd, 2023 to February 4th, 2023. And save the data in a file with path "./data/test.parquet".

```
python cyan_extract.py -datefrom 20230202 -dateto 20230204 -path test.parquet
```

## Data Analysis Dashboard

Example: Run code below to activate dashboard with data file "./data/L3B_CYAN_DAILY_mendota.parquet".

```
python dashboard.py -path data/L3B_CYAN_DAILY_mendota.parquet
```

## Cyanobacteria Forecasting

Example: Run code below to generate forecast with data file "./data/L3B_CYAN_DAILY_mendota.parquet".

```
python forecast.py -path data/L3B_CYAN_DAILY_mendota.parquet
```
