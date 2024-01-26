import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import requests

app = dash.Dash(__name__)

COVID_API_URL = "http://127.0.0.1:5000/covid_cases"
AQI_API_URL = "http://127.0.0.1:5000/aqi_data"

months_options = [
    {'label': 'February - September 2020', 'value': '2020-02-01_to_2020-08-31'},
    {'label': 'February 2020', 'value': '2020-02'},
    {'label': 'March 2020', 'value': '2020-03'},
    {'label': 'April 2020', 'value': '2020-04'},
    {'label': 'May 2020', 'value': '2020-05'},
    {'label': 'June 2020', 'value': '2020-06'},
    {'label': 'July 2020', 'value': '2020-07'},
    {'label': 'August 2020', 'value': '2020-08'},
]

cached_covid_data = None
cached_aqi_data = None

def fetch_data():
    global cached_covid_data, cached_aqi_data

    # Fetching COVID-19 data for New York
    response = requests.get(COVID_API_URL)
    cached_covid_data = pd.DataFrame(response.json())

    # Fetching Air Quality data for New York
    response = requests.get(AQI_API_URL)
    cached_aqi_data = pd.DataFrame(response.json())


    cached_covid_data['DATE'] = pd.to_datetime(cached_covid_data['DATE'])
    cached_aqi_data['Date'] = pd.to_datetime(cached_aqi_data['Date'])


fetch_data()

app.layout = html.Div([
    html.H1("COVID-19 Cases and Air Quality in New York", style={'text-align': 'center'}),
    dcc.Dropdown(
        id='month-selector',
        options=months_options,
        value='2020-02-01_to_2020-08-31'
    ),
    dcc.Graph(id='covid-aqi-graph')
])

@app.callback(
    Output('covid-aqi-graph', 'figure'),
    [Input('month-selector', 'value')]
)


def update_graph(selected_month):
    global cached_covid_data, cached_aqi_data

    if selected_month == '2020-02-01_to_2020-08-31':
        start_date = '2020-02-01'
        end_date = '2020-09-01'
    else:
        start_date = pd.to_datetime(selected_month + '-01')
        end_date = start_date + pd.offsets.MonthEnd()

    covid_data_filtered = cached_covid_data[(cached_covid_data['DATE'] >= start_date) & (cached_covid_data['DATE'] <= end_date)]
    aqi_data_filtered = cached_aqi_data[(cached_aqi_data['Date'] >= start_date) & (cached_aqi_data['Date'] <= end_date)]

    window_size = 7  # 7-day moving average
    covid_data_filtered['7_day_avg'] = covid_data_filtered['CASES'].rolling(window=window_size).mean()

    fig = go.Figure()

    # COVID-19 Cases Line
    fig.add_trace(go.Scatter(x=covid_data_filtered['DATE'], y=covid_data_filtered['CASES'],
                             mode='lines',
                             name='COVID-19 Cases'))

    # Air Quality Line
    fig.add_trace(go.Scatter(x=aqi_data_filtered['Date'], y=aqi_data_filtered['MAXAQI'],
                             mode='lines',
                             name='Air Quality Index',
                             yaxis='y2'))

    fig.add_trace(go.Scatter(x=covid_data_filtered['DATE'], y=covid_data_filtered['7_day_avg'],
                             mode='lines',
                             name='7-Day Moving Average',
                             line=dict(color='orange', width=2, dash='dash')))

    # Layout settings
    fig.update_layout(
        xaxis=dict(title='Date'),
        yaxis=dict(title='COVID-19 Cases'),
        yaxis2=dict(title='AQI Value', side='right', overlaying='y'),
        title='Daily Active COVID-19 Cases vs Air Quality Index in New York',
        hovermode='closest'
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
