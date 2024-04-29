import datetime
import pandas as pd
import numpy as np
import pmdarima as pm
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels.tsa.seasonal as sts
import plotly.express as px
from plotly.subplots import make_subplots


def prep_data(df: pd.DataFrame):
    """
    Prepare data for time-series model: transform to weekly, impute missing week, log-transform ci values
    """

    # aggreate data to daily then weekly
    df['date'] = pd.to_datetime(df['date'])
    df_daily = df.groupby('date').agg(
        CI_cyano=('CI_cyano', 'mean')).reset_index()
    df_daily['month'] = df_daily.date.dt.month
    df_daily['week'] = df_daily.date.dt.isocalendar().week
    df_daily['year'] = df_daily.date.dt.isocalendar().year
    df_weekly = df_daily.groupby(['year', 'week']).agg(
        date=('date', 'min'), CI_cyano=('CI_cyano', 'mean')).reset_index()
    df_weekly = df_weekly.sort_values(by='date')
    df_weekly['year'] = df_weekly['year'].astype(int)
    df_weekly['week'] = df_weekly['week'].astype(int)

    # impute missing weeks with mean
    week_first = df_weekly[df_weekly.date ==
                           df_weekly.date.min()].week.values[0]
    week_last = df_weekly[df_weekly.date ==
                          df_weekly.date.max()].week.values[0]
    years = df_weekly.year.unique()

    df_weekly_imp = df_weekly.copy()
    append_rows = {'year': [], 'week': [], 'date': []}

    cicyano_mean = df_weekly.groupby('week').CI_cyano.mean().reset_index()
    cicyano_mean['week'] = cicyano_mean['week'].astype(int)

    for w in range(1, 53):
        if w < week_first:
            yy = years[1:]
        elif w > week_last:
            yy = years[:-1]
        else:
            yy = years
        tmpdf = df_weekly_imp[df_weekly_imp.week == w]
        y_avg = tmpdf.CI_cyano.mean()
        for y in yy:
            tmpdf2 = tmpdf[tmpdf.year == y]
            if len(tmpdf2) == 0:
                append_rows['year'].append(y)
                append_rows['week'].append(w)
                append_rows['date'].append(datetime.datetime.strptime(
                    str(y)+'-W'+str(w)+'-1', '%G-W%V-%u'))

    df_append = pd.DataFrame(append_rows)
    df_append['week'] = df_append['week'].astype(int)

    df_append = pd.merge_asof(
        left=df_append, right=cicyano_mean, on='week', direction='nearest')
    df_weekly_imp = pd.concat(
        [df_weekly_imp, df_append], axis=0, ignore_index=True)
    df_weekly_imp = df_weekly_imp.sort_values(by='date').reset_index(drop=True)

    # log-transform ci cyano values
    df_weekly_imp['log_y'] = np.log(df_weekly_imp.CI_cyano)

    return df_weekly_imp


# Seasonality & Trend Decomposition
def decomp_ts(ts, period=52, model='additive'):
    res = sts.seasonal_decompose(ts, period=period, model=model)

    # Create separate line plots for trend, seasonal, and residual components
    fig1 = px.line(x=ts.index, y=ts, labels={
                   'x': 'Date', 'y': 'CI_cyano'}, title='CI_cyano')
    fig2 = px.line(x=ts.index, y=res.trend, labels={
                   'x': 'Date', 'y': 'Trend'}, title='Trend')
    fig3 = px.line(x=ts.index, y=res.seasonal, labels={
                   'x': 'Date', 'y': 'Seasonal'}, title='Seasonal')
    fig4 = px.scatter(x=ts.index, y=res.resid, labels={
                      'x': 'Date', 'y': 'Residual'}, title='Residual')

    # Combine fig1-4 as subplots
    fig = make_subplots(rows=4, cols=1, subplot_titles=('CI_cyano', 'Trend', 'Seasonal', 'Residual'
                                                        ))
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)
    for trace in fig2.data:
        fig.add_trace(trace, row=2, col=1)
    for trace in fig3.data:
        fig.add_trace(trace, row=3, col=1)
    for trace in fig4.data:
        fig.add_trace(trace, row=4, col=1)

    # Set layout properties
    fig.update_layout(
        showlegend=True, title_text="Seasonality & Trend Decomposition")
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="CI_cyano", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Trend", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Seasonal", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=4, col=1)
    fig.update_yaxes(title_text="Residual", row=4, col=1)
    fig.add_hline(y=0, row=4, col=1)
    fig.show()


# Train SARIMA model
def train(d_in: pd.DataFrame):
    """
    Predict CI_cyano each coordinate of the area for the next n days
    Return data: actual data, df_fcst: forecasted output
    """
    # Prepare dataset for model fitting
    df = d_in.copy()

    # tune the hyperparameters of the SARIMA model
    best_model = pm.auto_arima(df.log_y,
                               max_p=2, max_q=2,
                               max_P=2, max_Q=2,
                               m=52, seasonal=True,
                               d=0, D=1, trace=True,
                               information_criterion='bic',
                               error_action='ignore',
                               suppress_warnings=True,
                               stepwise=True)

    a_order = best_model.get_params()['order']
    s_order = best_model.get_params()['seasonal_order']
    c_trend = None
    if best_model.get_params()['with_intercept']:
        c_trend = 'c'

    model_name = 'SARIMA'+str(a_order)+'x'+str(s_order)

    smodel = SARIMAX(df.log_y, order=a_order,
                     seasonal_order=s_order, trend=c_trend).fit(disp=False)

    return model_name, smodel


# make predictions with SARIMA model
def predict(d_in: pd.DataFrame, mod, n=12):
    sfitted = mod.get_prediction(
        start=d_in.index[0], end=d_in.index[-1], dynamic=False).conf_int()
    sfitted = np.exp(sfitted.astype(np.float128))
    sfitted['log_yhat'] = mod.fittedvalues
    sfitted['yhat'] = np.exp(mod.fittedvalues)
    dfitted = pd.concat([d_in, sfitted], axis=1)
    dfitted = dfitted.rename(
        columns={'lower log_y': 'yhat_lower', 'upper log_y': 'yhat_upper'})

    dfcst = mod.get_forecast(n, dynamic=True).summary_frame()

    dfcst['date'] = [d_in.date.max() + datetime.timedelta(days=7*(i+1))
                     for i in range(len(dfcst))]
    dfcst['yhat'] = np.exp(dfcst['mean'])
    dfcst['yhat_lower'] = np.exp(dfcst['mean_ci_lower'])
    dfcst['yhat_upper'] = np.exp(dfcst['mean_ci_upper'])
    dfcst = dfcst.rename(columns={"mean": "log_yhat"})

    return dfitted, dfcst


def plot_fcst(dfitted, dfcst, model_name):
    HAB_HIGH = 0.016
    HAB_MED = 0.001

    # Plot training data and model predictions
    fig1 = px.line(dfitted, x='date', y='CI_cyano', labels={
                   'date': 'Date', 'CI_cyano': 'CI_cyano'})
    fig1.add_scatter(x=dfitted.date[53:], y=dfitted.yhat[53:], mode='lines', name='Model fitted values',
                     line=dict(color='green', dash='dash'))

    # Plot forecast data
    weeks2plot = 52
    fig2 = px.line(dfitted[-weeks2plot:], x='date', y='CI_cyano',
                   labels={'date': 'Date', 'CI_cyano': 'CI_cyano'})
    fig2.add_scatter(x=dfcst.date, y=dfcst.yhat, mode='lines', name='CI_cyano forecast',
                     line=dict(color='green'))
    fig2.add_scatter(x=dfitted[-weeks2plot:].date, y=dfitted[-weeks2plot:].CI_cyano, mode='lines', name='CI_cyano actual',
                     line=dict(color='blue'))

    # Combine fig1 and fig2 as subplots
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Historical data & model predictions",
                                                        "Cyanobacteria Forecast for next "+str(len(dfcst))+" weeks"))
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)
    for trace in fig2.data:
        fig.add_trace(trace, row=2, col=1)

    # Set layout properties
    fig.update_layout(
        showlegend=True, title_text="Cyanobacteria Forecast with Model: " + model_name)
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="CI_cyano", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="CI_cyano", row=2, col=1)
    fig.add_vline(x=dfitted.date[-1:].values,
                  line_dash='dot', line_color='black', row=2, col=1)

    if max(dfitted.CI_cyano.max(), dfitted.yhat[53:].max()) >= HAB_MED:
        fig.add_hline(y=HAB_MED, line_dash='dot', line_color='orange',
                      annotation_text='HAB Medium', annotation_position='bottom left', row=1, col=1)
    if max(dfitted.CI_cyano.max(), dfitted.yhat[53:].max()) >= HAB_HIGH:
        fig.add_hline(y=HAB_HIGH, line_dash='dot', line_color='red',
                      annotation_text='HAB High', annotation_position='bottom left', row=1, col=1)

    if max(dfitted[-weeks2plot:].CI_cyano.max(), dfcst.yhat.max()) >= HAB_MED:
        fig.add_hline(y=HAB_MED, line_dash='dot', line_color='orange',
                      annotation_text='HAB Medium', annotation_position='bottom left', row=2, col=1)
    if max(dfitted[-weeks2plot:].CI_cyano.max(), dfcst.yhat.max()) >= HAB_HIGH:
        fig2.add_hline(y=HAB_HIGH, line_dash='dot', line_color='red',
                       annotation_text='HAB High', annotation_position='bottom left', row=2, col=1)

    fig.show()
