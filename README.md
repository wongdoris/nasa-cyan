# CYANOBACTERIA ASSESSMENT NETWORK (CYAN)
### Link: https://oceancolor.gsfc.nasa.gov/about/projects/cyan/

## Cyanobacteria Analysis with NASA CYAN Data
This project focuses on analyzing the L3B satellite data from the CYAN project to gain insights and forecast cyanobacteria levels in freshwater lakes across North America.
- Data Preprocessing: Collect L3B daily data from NASA Ocean Color, convert to tabular format, and stack them together. Sample data provided for Lake Mendota (Wisconsin) and Jordan Lake (North Carolina) for May 2016 to April 2024.
- Data Analysis: Spatial and temporal trends for the cyanobacteria levels in freshwater lakes.
- Cyanobacteria Forecasting: use SARIMA model for time series forecasting. 
- Interactive Dashboard: An interactive dashboard is presented to visualize findings.

## Clone the Repository
```
git clone https://github.com/wongdoris/nasa-cyan.git

## install requirements:
cd nasa-cyan
pip install -r requirements.txt
```

## Extract Data from CYAN Project
Run the script below to extract L3B_CYAN_DAILY data for February 2 - 4, 2023. Save the data in .parquet format via path "./data/test.parquet".

```
python cyan_extract.py -datefrom 20230202 -dateto 20230204 -path test.parquet
```

## Data Analysis Dashboard
Run the script below to activate dashboard via sample data file "./data/L3B_CYAN_DAILY_MENDOTA.parquet".

```
python dashboard.py -path data/L3B_CYAN_DAILY_MENDOTA.parquet
```

## Cyanobacteria Forecasting
Run the script below to generate forecast via sample data file "./data/L3B_CYAN_DAILY_mendota.parquet".

```
python forecast.py -path data/L3B_CYAN_DAILY_MENDOTA.parquet
```
