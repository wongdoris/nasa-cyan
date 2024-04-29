import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from utils import dataprep

app = dash.Dash(__name__)

# file = 'data/L3B_CYAN_DAILY_JORDAN.parquet'
file = 'data/L3B_CYAN_DAILY_MENDOTA.parquet'
# file = 'data/L3B_CYAN_DAILY_MATT.parquet'

df = dataprep.getdata(file)
df = dataprep.hab_level(df)

# Descriptive statistics
stats = df.groupby('date').agg(nobs=('clat', 'count'),
                               avg_CI_cyano=('CI_cyano', 'mean'),
                               min_CI_cyano=('CI_cyano', 'min'),
                               max_CI_cyano=('CI_cyano', 'max'),
                               ).reset_index().tail(10)

x_range = df.clon.max()-df.clon.min()
y_range = df.clat.max()-df.clat.min()
pltf = 500
pltw = pltf*(x_range/0.1)
plth = pltf*(y_range/0.1)


p1 = df.groupby('date').CI_cyano.mean().reset_index()

df_day = df.groupby('date').agg(CI_cyano=('CI_cyano', 'mean'),
                                nobs=('clat', 'count'),
                                hab_high=('HAB_HIGH', 'sum'),
                                hab_high_med=('HAB_HIGH_MED', 'sum')).reset_index()
df_day['year'] = df_day.date.dt.year
df_day['month'] = df_day.date.dt.month
df_day['pct_hab_high'] = df_day.hab_high/df_day.nobs
df_day['pct_hab_high_med'] = df_day.hab_high_med/df_day.nobs

p2 = df_day.pivot_table(index='year', columns='month', values='CI_cyano',
                        aggfunc='mean', margins=True, margins_name='Average')
p2.columns = list(p2.columns[:-1])+[13]
p2.index = list(p2.index[:-1])+[p2.index[:-1].max()+1]
xticks = p2.columns[:-1].tolist()+['Average']
yticks = p2.index[:-1].tolist()

p3 = df_day.pivot_table(index='year', columns='month', values='nobs',
                        aggfunc='sum', margins=False)

pltw2 = 1300
plth2 = len(p2)*50

df_loc = df.groupby(['clat', 'clon']).agg(CI_cyano=('CI_cyano', 'mean'),
                                          CI_cyano_median=(
    'CI_cyano', 'median'),
    nobs=('date', 'count'),
    hab_high=('HAB_HIGH', 'sum'),
    hab_high_med=('HAB_HIGH_MED', 'sum')).reset_index()
df_loc['pct_hab_high'] = df_loc.hab_high/df_loc.nobs
df_loc['pct_hab_high_med'] = df_loc.hab_high_med/df_loc.nobs


# Define the layout of the app
app.layout = html.Div([
    html.H1(file),

    # Descriptive statistics
    html.Div([
        html.H3(
            (f'Longitude: [{min(df.clon):.4f}, {max(df.clon):.4f}]      Latitude: [{min(df.clat):.4f}, {max(df.clat):.4f}]\n'),
        )
    ], style={'width': '100%', 'display': 'inline-block'}),


    html.H2("Select Date Range:"),

    html.Div([
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=df['date'].min(),
            end_date=df['date'].max(),
            display_format='YYYY-MM-DD',
            style={'display': 'inline-block', 'width': '100%'}
        ),
        html.Div(id='text', style={
                 'display': 'inline-block', 'width': '100%', 'vertical-align': 'top', 'text-align': 'left', 'white-space': 'pre-line', "font-weight": "bold", "font-size": 16}),
        dcc.Graph(id='scatter-plot',
                  style={'display': 'inline-block', 'width': '100%'}),
        dcc.Graph(id='line-plot',
                  style={'display': 'inline-block', 'width': '100%'}),
    ], className='six columns'),

    html.Div([
        dcc.Graph(
            id='heatmap-cyano',
            figure={
                'data': [
                    go.Heatmap(
                        z=p2.values,
                        x=p2.columns,
                        y=p2.index,
                        colorscale='Spectral_r',
                        zmin=p2.values.min(),
                        zmax=p2.values.max(),
                        zhoverformat='.6f',
                        texttemplate="%{z:.4f}"
                    )
                ],
                'layout': go.Layout(
                    title='Average Cyanobacteria Level by month',
                    width=pltw2, height=plth2,
                    xaxis=dict(title='Month', ticktext=xticks),
                    yaxis=dict(title='Year', ticktext=yticks,
                               autorange='reversed'),
                )
            }
        )
    ], className='six columns'),

    html.Div([
        dcc.Graph(
            id='heatmap-obs',
            figure={
                'data': [
                    go.Heatmap(
                        z=p3.values,
                        x=p3.columns,
                        y=p3.index,
                        colorscale='Spectral_r',
                        zmin=p3.values.min(),
                        zmax=p3.values.max(),
                        zhoverformat=',',
                        texttemplate="%{z:,}"
                    )
                ],
                'layout': go.Layout(
                    title='No. Observations by month',
                    width=pltw2, height=plth2,
                    xaxis=dict(title='Month', ticktext=xticks),
                    yaxis=dict(title='Year', ticktext=yticks,
                               autorange='reversed'),
                )
            }
        )
    ], className='six columns'),


], className='row')


@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('line-plot', 'figure'),
     Output('text', 'children')],
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_scatter_plot(start_date, end_date):
    df2 = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    filtered_df = df2.groupby(['clat', 'clon']).agg(
        CI_cyano=('CI_cyano', 'mean'), nobs=('CI_cyano', 'count')).reset_index()
    filtered_df2 = df2.groupby('date').CI_cyano.mean().reset_index()

    # Create subplots
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('No. Observations', 'Average CI_cyano'))

    # Add traces to subplot 1
    fig.add_trace(
        go.Scatter(
            x=filtered_df['clon'],
            y=filtered_df['clat'],
            mode='markers',
            marker=dict(
                size=9,
                color=filtered_df.nobs,
                colorscale='Spectral_r',
                showscale=True,
                opacity=0.8,
                coloraxis='coloraxis'
            ),
            text=filtered_df['nobs'].apply(
                lambda x: f'No. observations: {x:,}'),
            hoverinfo='text+x+y'
        ),
        row=1, col=1
    )

    # Add traces to subplot 2
    fig.add_trace(
        go.Scatter(
            x=filtered_df.clon,
            y=filtered_df.clat,
            mode='markers',
            marker=dict(
                size=8,
                color=filtered_df.CI_cyano,
                colorscale='Spectral_r',
                showscale=True,
                opacity=0.8,
                coloraxis='coloraxis2'
            ),
            text=filtered_df['CI_cyano'].apply(
                lambda x: f'CI_cyano: {x:.6f}'),
            hoverinfo='text+x+y'
        ),
        row=1, col=2
    )

    # Update subplot layout
    fig.update_layout(
        title='Cyanobacteria Levels by Longitude/Latitude locations',
        width=pltw*1.7, height=plth,
        coloraxis=dict(colorscale='Spectral_r', colorbar_x=0.45,
                       colorbar_thickness=23),
        coloraxis2=dict(colorscale='Spectral_r',
                        colorbar_x=1, colorbar_thickness=23)
    )

    fig.update_xaxes(title_text="Longitude", row=1, col=1)
    fig.update_yaxes(title_text="Latitude", row=1, col=1)
    fig.update_xaxes(title_text="Longitude", row=1, col=2)
    fig.update_yaxes(visible=True, showticklabels=False, row=1, col=2)

    fig2 = go.Figure(data=go.Scatter(
        x=filtered_df2.date,
        y=filtered_df2.CI_cyano,
        mode='lines',
        name='CI_cyano',
        text=filtered_df2['CI_cyano'].apply(
            lambda x: f'CI_cyano: {x:.6f}'),
        hoverinfo='text+x'
    ))
    fig2.update_layout(title='Daily Average Cyanobacteria Level',
                       xaxis_title='date', yaxis_title='CI_cyano')

    text = f"\nNo. of observations: {len(df2):,.0f}" + \
        f"\nNo. of pixels: {len(filtered_df):,.0f}" + \
        f"\nCI cyano - average: {filtered_df.CI_cyano.mean():.6f}" + \
        f"\nCI cyano - minimum: {filtered_df.CI_cyano.min():.6f}" + \
        f"\nCI cyano - maximum: {filtered_df.CI_cyano.max():.6f}"

    return fig, fig2, text


if __name__ == '__main__':
    app.run_server(debug=True)
