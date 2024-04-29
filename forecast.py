
import pandas as pd
from utils import dataprep, sarima

file = 'data/L3B_CYAN_DAILY_JORDAN.parquet'

# extract data
print("Extracting data...")
df = dataprep.getdata(file)
print("Extracted data size:", df.shape)

# prepare data
print("\nPreprocessing data...")
df_weekly_imp = sarima.prep_data(df)
print("Processed data size:", df_weekly_imp.shape)

# train SARIMA model
print("\nOptimizing SARIMA model...")
model_name, smodel = sarima.train(df_weekly_imp)
print("Final model:", model_name)

# generate predictions
print("\nGenerating predictions...")
nweeks = 12
dfitted, dfcst = sarima.predict(df_weekly_imp, smodel, n=nweeks)
print(f"Forecast for the next {nweeks} weeks:\n")
dfcst_show = pd.DataFrame({'CI_cyano forecast': dfcst.yhat.values,
                           'lower bound': dfcst.yhat_lower.values,
                           'upper bound': dfcst.yhat_upper.values, }, index=dfcst.date.values)
print(dfcst_show)

# plot forecast and decomposition
sarima.decomp_ts(df_weekly_imp.set_index('date').CI_cyano)
sarima.plot_fcst(dfitted, dfcst, model_name)
