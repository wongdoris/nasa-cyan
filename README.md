# nasa-cyan
Cyanobacteria analysis with NASA CYAN data

To run analysis dashboard:
```python dashboard.py -path data/L3B_CYAN_DAILY_mendota.parquet```

To generate Cyanobacteria forecast:
```python forecast.py -path data/L3B_CYAN_DAILY_mendota.parquet```

To download data from CYAN project:
```python cyan_extract.py```

## Using Google Colab:
Clone the repository and install requirements:
```
%cd /content/
!git clone https://github.com/wongdoris/nasa-cyan.git
%cd /content/nasa-cyan
!pip install -r requirements.txt
```