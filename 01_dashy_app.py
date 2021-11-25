# -*- coding: utf-8 -*-
"""
Created on Wed Nov 24 11:28:01 2021

@author: Jansen Zhang
"""

# -------------- Load packages --------------------

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_table

import plotly.graph_objects as go
# To render plots to browser
# import plotly.io as pio
# pio.renderers.default = "browser"

import pandas as pd
import numpy as np
# Tell pandas to print more columns
# pd.set_option('display.max_columns', 500)

from datetime import date, timedelta


# -------------- Assumptions -----------------------

secondary_github_data_web = 'https://raw.githubusercontent.com/M3IT/COVID-19_Data/master/Data/COVID_AU_state.csv'

assum_days_to_show = 60
assum_start_date = pd.to_datetime('today') - timedelta(days = assum_days_to_show)

# Assumption for length of incubation period in days
# Literature seems to suggest between 5-7 days
assum_incubation_days = 5

# ---------- Load and process data ------------------
raw_covid_df = pd.read_csv(secondary_github_data_web)

# Convert date to datetime format
raw_covid_df['date'] =  pd.to_datetime(raw_covid_df['date'], format='%Y-%m-%d')

# Compute max_date in data
max_date = max(raw_covid_df["date"])

# ------------- Initialize the app --------------------

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

# ------------- App layout ------------------------
header_height = "4rem"
sidebar_width = "19vw"

# style arguments for header
HEADER_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": header_height,
    "padding": "1rem 1rem",
    "background-color": "#E8E8E8",
}

# the style arguments for the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": header_height,
    "left": 0,
    "bottom": 0,
    "width": sidebar_width,
    "padding": "1rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "position": "fixed",
    "top": header_height,
    "margin-left": sidebar_width,
    "padding": "1rem 1rem",
}

header = html.Div([
    html.H3('COVID-19 case tracker', style={"vertical-align": "middle"})
    ], style=HEADER_STYLE
)

sidebar = html.Div(
    [
        html.P("Select inputs:"),
        html.Div([
            html.Label(['State'], style={'font-weight': 'bold'}),
            dcc.Dropdown(id='input_location',
                         options=[
                             {'label': 'NSW', 'value': 'NSW'},
                             {'label': 'VIC', 'value': 'VIC'}
                         ],
                         value='NSW',
                         searchable=True,
                         style={"margin-bottom": "10px", 'width': 180})
        ]),
        html.Div([
            html.Label(['Days to project'], style={'font-weight': 'bold'}),
            dcc.Input(id='input_days_to_project',
                      value=14,
                      type='number',
                      min=1,
                      style={"margin-bottom": "10px", 'width': 180})
        ]),
        # html.Div([
        #     html.Label(['R_eff'], style={'font-weight': 'bold', 'margin-right': 100}), # 100 to move Input next line
        #     dcc.Input(id='input_R_eff',
        #               value=1,
        #               type='number',
        #               min=0.5,
        #               max=3,
        #               step=0.01,
        #               style={"margin-bottom": "10px", 'width': 180})
        # ])
    ],
    style=SIDEBAR_STYLE
)

# styling to make tabs a reasonable height
tab_height = '5vh'
TAB_STYLE = {'padding': '0',
             'line-height': tab_height}
TAB_SELECTED_STYLE = {'padding': '0',
                      'line-height': tab_height}

content = html.Div(
    id="page-content"
    , children = [
        dcc.Tabs(
            style = {'width': '40%','height':tab_height},
            children = [
                # Main tab
                dcc.Tab(label = 'Projected cases'
                    , style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE
                    , children = [
                    html.P(""),
                    html.Div(id='text_projected_chart_title', style={"width": "80vw", 'font-weight': 'bold'}),
                    html.Div(id='text_R_eff_print'),
                    dcc.Graph(
                        id='fig_projected_chart',
                    )
                ]),

                # Data table
                dcc.Tab(label = 'Data'
                        , style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE
                        , children = [
                        html.P(""),
                        #html.P("Showing " + str(assum_days_to_show) + " days of data:", style={"width": "70vw"}),
                        html.P("Showing full data source:", style={"width": "77vw"}),
                        dash_table.DataTable(
                            data=raw_covid_df.to_dict('records'),
                            columns=[{"name": i, "id": i} for i in raw_covid_df.columns],
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            page_action="native",
                            page_current=0,
                            page_size=10,
                            style_table={'overflowX': 'auto',
                                         "width": "77vw"},
                        )
                    ]),

                # About text tab
                dcc.Tab(label = 'About'
                    , style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE
                    , children = [
                        html.P(""),
                        html.P("About", style={"width": "80vw"})
                ])
        ]),

    ],
    style=CONTENT_STYLE
)

app.layout = html.Div([
    header,
    sidebar,
    content,

    # dcc.Store stores the intermediate data
    dcc.Store(id='intermediate_data'),
    dcc.Store(id='est_curr_R_eff')
])


# --------------- Functions -------------------
# Function: Collect required columns (report_date/location/daily_cases)
def process_data(p_data, p_location):
    processed_data = p_data

    # Filter to location and subset required cols
    processed_data = (
        processed_data.query("state_abbrev == @p_location") \
            .filter(["date", "state_abbrev", "confirmed"])
            .sort_values('date', ascending=1)
    )

    # Rename cols
    req_cols = ["report_date", "location", "daily_cases"]
    processed_data.columns = req_cols

    ## Fill in any missing values with 0
    processed_data["daily_cases"] = processed_data["daily_cases"].fillna(0)

    return processed_data

# Function: add smoothed trend column (smooth_cases)
def smooth_data(p_data, p_rolling_window):
    # Smooth data - compute 7 day average.
    # We want to apply smoothing to remove effect of daily variability as well as the weekly Monday dip

    smoothed_data = p_data

    smoothed_data["smooth_cases"] = smoothed_data["daily_cases"].rolling(p_rolling_window) \
        .mean() \
        .round(0)

    # Filter only last [assum_start_date = 60] days - also drops NaNs from rolling avg so we can convert to int
    smoothed_data = smoothed_data.query("report_date >= @assum_start_date")
    smoothed_data["smooth_cases"] = smoothed_data["smooth_cases"].astype(int)

    return smoothed_data

# Function - Simple estimate of current effective reproductive factor of the virus, based on the growth rate over the
# last [assum_incubation_days = 5] days
def estimate_R_eff(p_data, p_assum_incubation_days):
    max_date = max(p_data["report_date"])
    lag_date = max_date - timedelta(days=p_assum_incubation_days)

    curr_cases = p_data[p_data["report_date"] == max_date]["smooth_cases"].values[0]
    lag_cases = p_data[p_data["report_date"] == lag_date]["smooth_cases"].values[0]

    R_eff = (curr_cases / lag_cases) ** (1 / assum_incubation_days)

    R_eff = round(R_eff, 2)

    return R_eff

# Function - Project cases - projection is based on exponential growth with factor
# p_R_eff/p_assum_incubation_days
def project_cases_from_R_eff(p_days_to_project, p_data, p_R_eff, p_assum_incubation_days):

    # Convert to date (to be safe)
    p_data['report_date'] = pd.to_datetime(p_data['report_date'], format='%Y-%m-%d')

    # Current date and cases
    curr_date = max(p_data["report_date"])
    curr_cases = p_data[p_data["report_date"] == curr_date]["smooth_cases"].values[0]

    # Projected date and cases -
    proj_date = pd.Series(range(1, p_days_to_project + 1))

    proj_cases = curr_cases * p_R_eff ** (proj_date / p_assum_incubation_days)
    proj_cases = round(proj_cases, 0).astype(int)

    proj_date = curr_date + pd.to_timedelta(proj_date, unit='d')

    # Collate into dataframe
    location = p_data["location"].unique()

    projected_df = {
        'report_date': proj_date.values
        , 'location': np.repeat(location, p_days_to_project)
        , 'daily_cases': np.repeat(np.NaN, p_days_to_project)
        , 'smooth_cases': np.repeat(np.NaN, p_days_to_project)
        , 'projected_cases': proj_cases.values
    }
    projected_df = pd.DataFrame(projected_df)

    new_data = pd.concat([p_data, projected_df])

    return new_data

### Function: Plot projected claiming
def plot_projected_claims(p_data):

    plot_data = p_data

    fig = go.Figure()

    # Trace for daily cases
    fig.add_trace(
        go.Scatter(x=plot_data['report_date']
                   , y=plot_data['daily_cases']
                   , mode="lines"
                   , name="Reported cases"))

    # Trace for smoothed cases
    fig.add_trace(
        go.Scatter(x=plot_data['report_date']
                   , y=plot_data['smooth_cases']
                   , mode="lines"
                   , name="Smoothed trend (7-day average)"))

    # Trace for projected cases
    fig.add_trace(
        go.Scatter(x=plot_data['report_date']
                   , y=plot_data['projected_cases']
                   , mode="lines"
                   , line=dict(dash='dash')
                   , name="Projected cases"))

    fig.update_yaxes(rangemode="tozero")

    #print_location = plot_data["location"].unique()[0]

    # Update chart title and labels
    fig.update_layout(
        #title="Projected " + print_location + " COVID-19 cases, extrapolated from simple estimate of R_eff"
        yaxis_title="Daily cases"
        , legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="left",
            x=0.2)
        , margin={'t': 15}
    )

    return fig


# ------------- App callbacks --------------------

# First callback to process data and update dataframe
@app.callback(
    [Output('intermediate_data', 'data'),
     Output('est_curr_R_eff', 'data')],
    [Input('input_location', 'value')]
)

def apply_user_inputs_to_data(input_location):

    print("apply_user_inputs_to_data")
    print(input_location)

    # Process data and fetch required cols (report_date/location/daily_cases)
    intermediate_data = process_data(p_data=raw_covid_df
                            , p_location=input_location)

    # Add smoothed trend
    intermediate_data = smooth_data(p_data=intermediate_data
                            , p_rolling_window=7)

    # Estimate current effective reproduction rate
    est_curr_R_eff = estimate_R_eff(p_data=intermediate_data
                                    , p_assum_incubation_days=assum_incubation_days
                                    )
    print(est_curr_R_eff)

    return intermediate_data.to_json(date_format='iso', orient='split'), est_curr_R_eff


# Second callback to plot chart from processed data
@app.callback(
    Output('fig_projected_chart', 'figure'),
    [Input('intermediate_data', 'data'),
     Input('est_curr_R_eff', 'data'),
     Input('input_days_to_project', 'value')]
)

def update_plot(intermediate_data, est_curr_R_eff, input_days_to_project):

    print("update_plot")

    # Read back in intermediate data stored from previous callback
    covid_df = pd.read_json(intermediate_data, orient='split')
    print(covid_df.head())
    print(est_curr_R_eff)

    # Add projections to covid_df
    covid_df = project_cases_from_R_eff(
        p_days_to_project=input_days_to_project
        , p_data=covid_df
        , p_R_eff=est_curr_R_eff
        , p_assum_incubation_days=assum_incubation_days
    )

    fig = plot_projected_claims(p_data = covid_df)
    #fig.show()
    print("fig ran")

    return fig

# Callbacks for text outputs
@app.callback(
    Output('text_projected_chart_title', 'children'),
    [Input('input_location', 'value')]
)

def print_chart_content_title(location):
    return 'Projected {} COVID-19 cases'.format(location)

@app.callback(
    Output('text_R_eff_print', 'children'),
    [Input('est_curr_R_eff', 'data')]
)

def print_chart_content_title(est_curr_R_eff):
    text = 'Projected cases are based on an estimated current R_eff  of ' + str(est_curr_R_eff) + \
            ' as at ' + str(date.strftime(max_date, '%d %B %Y')) + '.'
    return text
    #return 'Projected cases are based on an estimated current R_eff  of {} as at max_date.'.format(est_curr_R_eff)


# ------------------ Run app -----------------------
if __name__ == '__main__':
    app.run_server(debug=False)
