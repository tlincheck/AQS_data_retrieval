#%%  
### Load in necessary packages ###

# from toxicsdata_functions import unit_convert
from dash import Dash, html, dcc, html, callback, Output, Input # Dash components and callback functions
import plotly.graph_objects as go
import plotly.express as px # For plotting
import dash_ag_grid as dag # For interactive data tables
import numpy as np
import xarray as xr
import pandas as pd
import openpyxl
import glob as glob
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import seaborn as sns

#%%
### Load in processed data ###

data = 'merged_data_processed.csv'
df = pd.read_csv(data)

# %%
### CALCULATE QUARTERLY STATISTICS ###

# For each year/pollutant/site, calculate the quarterly mean and max values 

# Create an array of months
mon_arr = pd.to_datetime(df['Date']).dt.month

# Create a new column for quarter   
df['Quarter'] = pd.to_datetime(df['Date']).dt.to_period('Q')

# Create a new column for quarter number (1-4)
df['Quarter_Number'] = pd.to_datetime(df['Date']).dt.quarter

# Create a new column for year
df['Year'] = pd.to_datetime(df['Date']).dt.year

# Group by year, quarter, pollutant, and site, then calculate mean, max, and count
quarterly_stats = df.groupby(['Year', 'Quarter_Number', 'Parameter', 'Site ID']).agg(
    Sample_Average=('Sample Value', 'mean'),
    Sample_Max=('Sample Value', 'max'),
    Sample_Count=('Sample Value', 'count')
).reset_index() 

#%%

### Plot quarterly_stats as box and whisker plot ###

# Specified POLLUTANT and YEAR for plotting
yr = 2025
pollutant = 'Formaldehyde'

# Dataframe for specific pollutant and year
pollutant_df =df[(pd.to_datetime(df['Date']).dt.year == yr) & 
                       (df['Parameter'] == pollutant)].copy()

qt_data = quarterly_stats.loc[(quarterly_stats['Year']==2025) & (quarterly_stats['Parameter']=='Formaldehyde')].copy()


fig = px.box(pollutant_df, x="Quarter_Number", y="Sample Value", color="Site ID", points="all")
fig.show()

# Plotting Quarter Numbers on x axis, with grouped sites
fig2 = sns.boxplot(data=pollutant_df, x="Quarter_Number", y="Sample Value", hue="Site ID", points="all")
fig2.show()

# Plotting Sites on x axis, with grouped quarters
fig3 = px.box(pollutant_df, x="Site ID", y="Sample Value", color="Quarter_Number", points="all")
fig3.show()

# Get existing legend handles and labels to preserve box colors
handles, labels = plt.axes.get_legend_handles_labels()



#%%
# Plotting comparison of sites by quarter for one pollutant and year

pollutant_df['Site ID'] = pollutant_df['Site ID'].astype(str)
sites = sorted(pollutant_df['Site ID'].unique())
quarters = sorted(pollutant_df['Quarter_Number'].unique())

# for q in quarters:
#     df_q = pollutant_df[pollutant_df['Quarter_Number'] == q]
#     fig.add_trace(go.Box(
#     x=df_q['Site ID'], # x-axis is all Site IDs for quarter q
#     y=df_q['Sample Value'], 
#     name=f'Q{q}',
#     boxpoints='all', # show individual samples
#     jitter=0.3,
#     pointpos=0, # plot points over box
#     marker=dict(opacity=0.6, size=6),
#     offsetgroup=str(q),
#     legendgroup=str(q)
#     ))

#color_seq = px.colors.qualitative.Safe
# color_seq = [
#     '#1f78b4',  # darker blue
#     '#33a02c',  # green
#     '#e31a1c',  # red
#     '#ff7f00',  # orange
#     '#6a3d9a',  # purple
#     '#b15928'   # brown
# ]

color_seq = [
    '#d53e4f',  # dark pink
    '#7b3294',  # purple
    '#542788',  # deep purple
    '#8c510a',  # brown
    '#000000'   # black
]

fig = go.Figure()
for i, q in enumerate(quarters):
    df_q = pollutant_df[pollutant_df['Quarter_Number'] == q]
    color = color_seq[i % len(color_seq)]
    fig.add_trace(go.Box(
        x=df_q['Site ID'],
        y=df_q['Sample Value'],
        name=f'Q{q}',
        boxpoints='all',
        jitter=0.3,
        pointpos=0,
        marker=dict(color=color, opacity=0.8, size=6),
        line=dict(color=color),
        offsetgroup=str(q),
        legendgroup=str(q)
    ))

fig.update_layout(
title=f"{pollutant_df['Parameter'].iloc[0]} — Quarterly Samples by Site ({yr})",
xaxis_title='Site ID',
yaxis_title='Sample Value (' + (pollutant_df['Units'].iloc[0] if 'Units' in pollutant_df.columns else '') + ')',
boxmode='group', # group boxes of the same site together
xaxis=dict(categoryorder='array', categoryarray=sites),
width=1200,
height=600
)

fig.show()



# %%

# Initialize the app
app = Dash()


# App layout
app.layout = html.Div(children=[
    html.H1(children='Air Toxics Monitor Data App', style={'textAlign': 'center'}),

    # Dropdown component
    dcc.Dropdown(
        id='dropdown-menu',
        #options = dropdown_options,
        value = 43502,
        multi=False,
        ),

    dcc.Dropdown(
        id='yr-dropdown-menu',
        #options = yr_dropdown_opts,
        #value = list(yr_dropdown_opts.values())[-2],
        multi=False,
        ),


    dcc.Graph(
            id='param-scatter-plot',
            figure=fig,
            style={'height': '80vh', 'width': '100%'} # Set height/width of the container
            ), #=fig),

        html.Div(id='range-slider-container'),


])

import plotly.graph_objects as go
import plotly.express as px

# Filter for one year and parameter
year = 2025
parameter = 'Formaldehyde'

# Get raw data for scatter points
raw_data = df[(pd.to_datetime(df['Date']).dt.year == year) & 
              (df['Parameter'] == parameter)].copy()
raw_data['Year'] = pd.to_datetime(raw_data['Date']).dt.year
raw_data['Quarter'] = pd.to_datetime(raw_data['Date']).dt.quarter
raw_data['Quarter_Label'] = 'Q' + raw_data['Quarter'].astype(str)
raw_data['Site_Quarter'] = raw_data['Site ID'].astype(str) + '-' + raw_data['Quarter_Label']

# Get quarterly stats
quart_data = quarterly_stats[(quarterly_stats['Year'] == year) & 
                             (quarterly_stats['Parameter'] == parameter)].copy()
quart_data['Quarter_Label'] = 'Q' + quart_data['Quarter'].astype(str)
quart_data['Site_Quarter'] = quart_data['Site ID'].astype(str) + '-' + quart_data['Quarter_Label']

# Create figure with box plot
fig = go.Figure()

# Add box plot
fig.add_trace(go.Box(
    x=quart_data['Site_Quarter'],
    y=quart_data['Quarterly_Mean'],
    name='Quarterly Mean',
    boxmean='sd'
))

# Add individual sample points
fig.add_trace(go.Scatter(
    x=raw_data['Site_Quarter'],
    y=raw_data['Sample Value'],
    mode='markers',
    name='Individual Samples',
    marker=dict(size=5, opacity=0.5),
    jitter=0.3
))

fig.update_layout(
    title=f'{parameter} - Quarterly Data with Samples ({year})',
    xaxis_title='Site - Quarter',
    yaxis_title='Sample Value (ppbC)',
    height=600,
    hovermode='closest'
)

fig.show()