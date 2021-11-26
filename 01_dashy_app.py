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
import dash_daq as daq
import dash_table

import plotly.graph_objects as go
# To render plots to browser
# import plotly.io as pio
# pio.renderers.default = "browser"

import pandas as pd
import numpy as np
from pandas import Timestamp
# Tell pandas to print more columns
# pd.set_option('display.max_columns', 500)

import datetime
from datetime import date, timedelta


# -------------- Assumptions -----------------------

secondary_github_data_web = 'https://raw.githubusercontent.com/M3IT/COVID-19_Data/master/Data/COVID_AU_state.csv'

assum_days_to_show = 60
assum_start_date = pd.to_datetime('today') - timedelta(days = assum_days_to_show)

# Assumption for length of incubation period in days
# Literature seems to suggest between 5-7 days
assum_incubation_days = 5

# ---------- Load and process data ------------------

raw_covid_df = pd.read_csv(secondary_github_data_web)\
    .sort_values(by = ['date'], ascending = False)

# Compute max_date in data
max_date = max(raw_covid_df["date"])

# ------------- Initialize the app --------------------

app = dash.Dash(external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    { # font-awesome
            "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
            "rel": "stylesheet",
            "integrity": "sha512-iBBXm8fW90+nuLcSKlbmrPcLa0OT92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==",
            "crossorigin": "anonymous",
            "referrerpolicy": "no-referrer",
        }
])
app.config.suppress_callback_exceptions = True

# ------------- App layout ------------------------
# In Shiny, I would move all this UI stuff into a ui.R script - investigate best practice in Dash

### Styles ---

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

### Define UI - header, sidebar, content ---

header = html.Div([
    html.Div(html.I(className="fas fa-viruses", style={"font-size": "30px", "padding-right":"10px"}), style={'display': 'inline-block'}),
    html.Div(html.H3('COVID-19 case tracker', style={"vertical-align": "middle"}), style={'display': 'inline-block'})
    ], style=HEADER_STYLE
)

button_on_style = {'background-color':'green'}
button_off_style = {'background-color':'orange'}

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
        html.Div([
            html.Div([
                html.Label(['R_eff'], style={'font-weight': 'bold'})
            ]),
            html.Div([
                html.Button('Estimated', id='input_use_est', n_clicks=0, style= button_on_style),
                html.Button('Custom', id='input_use_cust', n_clicks=0, style = button_off_style)
            ], style = {'padding-bottom':'10px'}),
            #dcc.Input(id='input_cust_R_eff', type='number', min=0.01, max=10, step=0.01)
        ]),

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
        dcc.Tabs( # Tabs go under here as a subset of content
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
                dcc.Tab(label = 'Raw data'
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
                            style_header={'fontWeight': 'bold'},
                            style_cell={'font-family':'Segoe UI'},
                            style_table={'overflowX': 'auto',
                                         "width": "77vw"},
                            # fix left-most column getting cut off
                            css=[{'selector': '.row', 'rule': 'margin: 0'}]
                        )
                    ]),

                # About text tab
                dcc.Tab(label = 'About'
                    , style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE
                    , children = [
                        html.P(""),
                        html.P("This is a personal project to build a simple COVID-19 tracker for Australia using Dash Python.",
                               style={"width": "80vw"}),

                        html.P("Methodology", style={"font-weight": "bold"}),
                        html.P("To calculate a smooth trend, a simple methodology taking a rolling 7-day average of daily cases was applied to account for daily variability"
                               + " in reported cases as well as weekly seasonality (Monday dip in reported cases). ",
                               style={"width": "75vw"}),
                        html.P("R_eff (the effective viral reproduction rate) is estimated by R_eff(t_current) = [cases(t_current)/cases(t_current - incubation_period)]**(1/incubation_period)"
                               + ", with an assumed incubation period of 5 days based on most recent studies.",
                               style={"width": "75vw"}),
                        html.P("Projected cases extrapolates from the latest estimate of R_eff and assumes a flat growth rate. No adjustments are currently being made for changing"
                               + " real-world factors which may impact viral spread such as vaccination uptake, easing of restrictions or increased transmission during holiday periods.",
                               style={"width": "75vw"}),
                        html.P(""),

                        html.P("Data source", style = {"font-weight": "bold"}),
                        html.Div(html.P("Daily COVID-19 case data sourced from aggregated secondary source"), style = {"display":"inline-block", "padding-right":"4px"}),
                        html.Div(html.A(" here",
                               href="https://github.com/M3IT/COVID-19_Data",
                               target="_blank"),
                                 style={"display": "inline-block"}),
                        html.Div(html.P("."), style={"display": "inline-block"}),

                        html.P("Source code", style = {"font-weight": "bold"}),
                        html.Div(html.P("See Github repository for source code"),
                                 style={"display": "inline-block", "padding-right": "4px"}),
                        html.Div(html.A(" here",
                                        href="https://github.com/jansen-zhang20/covid_dashy_personal",
                                        target="_blank"),
                                 style={"display": "inline-block"}),
                        html.Div(html.P("."), style={"display": "inline-block"})

                    ])
        ]),

    ],
    style=CONTENT_STYLE
)

### Tie all together
app.layout = html.Div([
    header,
    sidebar,
    content,

    # dcc.Store stores the intermediate data
    dcc.Store(id='intermediate_data'),
    dcc.Store(id='est_curr_R_eff'),
    dcc.Store(id='store_estcust_mode')

])


# --------------- Functions used in callbacks -------------------
# For later on - a cleaner way of doing this would be to move these functions into a functions folder like I would in R

# Function: Collect required columns (report_date/location/daily_cases)
def process_data(p_data, p_location):
    processed_data = p_data

    # Convert date to datetime format
    processed_data['date'] = pd.to_datetime(processed_data['date'], format='%Y-%m-%d')

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

# Function: Add smoothed trend column (smooth_cases)
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
# In Shiny, all this would go into a server.R script - investigate best practice in Dash

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

# Intermediate callback to change button (estimated or custom R_eff) colours on click
# and store which button is clicked
@app.callback(
    [Output("input_use_est", "style"),
     Output("input_use_cust", "style"),
     Output("store_estcust_mode", "value")],
    [Input("input_use_est", "n_clicks"),
     Input("input_use_cust", "n_clicks")]
)
def set_active(est_clicks, cust_clicks): #*args
    ctx = dash.callback_context

    # get id of triggering button
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    print(button_id)
    print(est_clicks)
    print(cust_clicks)

    if (cust_clicks > 0) & (button_id == "input_use_cust"):
        return button_off_style, button_on_style, button_id
    else:
        button_id = "input_use_est"
        return button_on_style, button_off_style, button_id

# Second callback to plot chart from processed data
@app.callback(
    Output('fig_projected_chart', 'figure'),
    [Input('intermediate_data', 'data'),
     Input('est_curr_R_eff', 'data'),
     Input('input_days_to_project', 'value'),
     Input('store_estcust_mode', 'value')]
)

def update_plot(intermediate_data, est_curr_R_eff, input_days_to_project, store_estcust_mode):

    print("update_plot")

    # Read back in intermediate data stored from previous callback
    covid_df = pd.read_json(intermediate_data, orient='split')
    print(covid_df.head())
    print(est_curr_R_eff)

    if store_estcust_mode == "input_use_est":
        use_R_eff = est_curr_R_eff
    else:
        use_R_eff = 2

    # Add projections to covid_df
    covid_df = project_cases_from_R_eff(
        p_days_to_project=input_days_to_project
        , p_data=covid_df
        , p_R_eff=use_R_eff
        , p_assum_incubation_days=assum_incubation_days
    )

    fig = plot_projected_claims(p_data = covid_df)

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
    [Input('est_curr_R_eff', 'data'),
     Input('store_estcust_mode', 'value')]
)

def print_chart_content_title(est_curr_R_eff, store_estcust_mode):

    if store_estcust_mode == "input_use_est":
        insert = 'an estimated current R_eff  of ' + str(est_curr_R_eff)
    else:
        insert = 'inputted R_eff of ' + str(2)

    text = 'Projected cases are based on ' + insert + \
            ' as at ' + str(datetime.datetime.strptime(max_date, '%Y-%m-%d').strftime('%d %B %Y')) + '.'
    return text


# ------------------ Run app -----------------------
if __name__ == '__main__':
    app.run_server(debug=False)
