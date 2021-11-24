# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 14:02:21 2021

@author: Jansen Zhang
"""

# ---------- Load packages --------------
import pandas as pd
import numpy as np
from datetime import date, timedelta
#import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.express as px

# Tell pandas to print more columns
pd.set_option('display.max_columns', 500)

# Render plots to browser
import plotly.io as pio
pio.renderers.default = "browser"


# ---------- Load globals ---------------
secondary_github_data_web = 'https://raw.githubusercontent.com/M3IT/COVID-19_Data/master/Data/COVID_AU_state.csv'

assum_days_to_show = 60
assum_start_date = pd.to_datetime('today') - timedelta(days = assum_days_to_show)

# Assumption for length of incubation period in days
# Literature seems to suggest between 5-7 days
assum_incubation_days = 5


# ---------- Load data ------------------
raw_covid_df = pd.read_csv(secondary_github_data_web)


# ---------- Process data --------------
### Collect required columns (report_date/location/daily_cases) and add smoothed cases column (smooth_cases)

clean_covid_df = raw_covid_df

req_cols = ["report_date", "location", "daily_cases"]

# Convert date to datetime format
clean_covid_df['date'] =  pd.to_datetime(raw_covid_df['date'], format='%Y-%m-%d')

# Filter to NSW cases only and subset required cols
clean_covid_df = (
    clean_covid_df.query("state_abbrev == 'NSW'") \
                .filter(["date", "state_abbrev", "confirmed"])
                .sort_values('date', ascending=1)
 )

# Rename cols
clean_covid_df.columns = req_cols

## Fill in any missing values with 0 
clean_covid_df["daily_cases"] = clean_covid_df["daily_cases"].fillna(0)

# Smooth data - compute 7 day average.
# We want to apply smoothing to remove effect of daily variability as well as the weekly Monday dip
clean_covid_df["smooth_cases"] = clean_covid_df["daily_cases"].rolling(window=7) \
                                                                .mean() \
                                                                .round(0)

# Filter only last [assum_start_date = 60] days - also drops NaNs from rolling avg so we can convert to int
clean_covid_df = clean_covid_df.query("report_date >= @assum_start_date")
clean_covid_df["smooth_cases"] = clean_covid_df["smooth_cases"].astype(int)


# ----------- Project cases ---------------

### --- Set up functions we will use

# Function - Simple estimate of current effective reproductive factor of the virus, based on the growth rate over the
# last [assum_incubation_days = 5] days

def estimate_R_eff(p_data, p_assum_incubation_days):
    max_date = max(p_data["report_date"])
    lag_date = max_date - timedelta(days = p_assum_incubation_days)

    curr_cases = p_data[p_data["report_date"] == max_date]["smooth_cases"].values[0]
    lag_cases = p_data[p_data["report_date"] == lag_date]["smooth_cases"].values[0]

    R_eff = (curr_cases / lag_cases) ** (1 / assum_incubation_days)

    return(R_eff)


# Function - Project cases - projection is based on exponential growth with factor
# p_R_eff/p_assum_incubation_days

def project_cases_from_R_eff(p_days_to_project, p_data, p_R_eff, p_assum_incubation_days):

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

    return(new_data)


### --- Estimate current effective reproduction rate and add projections to cases dataframe
est_curr_R_eff = estimate_R_eff(p_data = clean_covid_df
                                , p_assum_incubation_days = assum_incubation_days
                                )

covid_df = project_cases_from_R_eff(
                        p_days_to_project = 14
                        , p_data = clean_covid_df
                        , p_R_eff = est_curr_R_eff
                        , p_assum_incubation_days = assum_incubation_days
                        )


# ----------- Produce plot ---------------
plot_data = covid_df

fig = go.Figure()

# Trace for daily cases
fig.add_trace(
    go.Scatter(x = plot_data['report_date']
              , y = plot_data['daily_cases']
              , mode = "lines"
              , name = "Daily reported cases"))

# Trace for smoothed cases
fig.add_trace(
    go.Scatter(x = plot_data['report_date']
              , y = plot_data['smooth_cases']
              , mode = "lines"
              , name = "Smoothed cases (7-day average)"))

# Trace for projected cases
fig.add_trace(
    go.Scatter(x = plot_data['report_date']
              , y = plot_data['projected_cases']
              , mode = "lines"
              , line=dict(dash='dash')
              , name = "Projected cases"))

fig.update_yaxes(rangemode="tozero")

print_location = plot_data["location"].unique()[0]

# Update chart title and labels
fig.update_layout(title = "Projected " + print_location + " COVID-19 cases, extrapolated from simple estimate of R_eff"
                  , xaxis_title = "Date"
                  , yaxis_title = "New cases")

fig.show()

