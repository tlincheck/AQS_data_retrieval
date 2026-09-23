#%%
from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from scipy import stats 
from scipy.stats import t as t_dist

# Incorporate the data
df = pd.read_csv('merged_data_processed.csv')
df['Date'] = pd.to_datetime(df['Date'])


### CALCULATE QUARTERLY STATISTICS ###
# For each year/pollutant/site, calculate the quarterly mean and max values 

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
    Sample_Count=('Sample Value', 'count'),
    Sample_Std=('Sample Value', 'std'), # sample standard deviation (SEM)
    Sample_sem=('Sample Value', 'sem') # standard error of the mean
).reset_index() 

# Confidence Interval (CI) Calculation:
# CI = sample mean ± (t-value * SEM))
# SEM = sample standard deviation / sqrt(sample size)

# Calculate the t-value for 95% confidence interval based on sample size
t_value = stats.t.ppf(0.975, df=quarterly_stats['Sample_Count'] - 1)  # two-tailed # 0.975 corresponds to (1 - alpha/2)

# Calculate the margin of error for the confidence interval
margin_of_error = t_value * (quarterly_stats['Sample_Std'] / np.sqrt(quarterly_stats['Sample_Count']))

# Calculate confidence intervals for each site and quarter
# quarterly_stats['Sample_CI_Lower'] = quarterly_stats['Sample_Average'] - 1.96 * (quarterly_stats['Sample_Std'] / np.sqrt(quarterly_stats['Sample_Count']))
quarterly_stats['Sample_CI_Lower'] = quarterly_stats['Sample_Average'] - margin_of_error
quarterly_stats['Sample_CI_Upper'] = quarterly_stats['Sample_Average'] + margin_of_error


#%% # Function to calculate 95% CI for quarterly data

# # Option 2: More efficient approach
def calculate_group_ci(group):
    """Calculate CI for grouped data"""
    values = group['Sample Value'].dropna()
    n = len(values)
    
    if n < 2: # If less than 2 samples
        return pd.Series({
            'Mean': np.nan,
            'Std': np.nan,
            'CI_Lower_95': np.nan,
            'CI_Upper_95': np.nan,
            'Count': n,
        })
    
    mean = values.mean()
    std = values.std(ddof=1)
    
    # scipy.stats.t.interval returns (lower, upper)
    ci_lower, ci_upper = t_dist.interval(
        confidence=0.95,
        df=n-1,
        loc=mean,
        scale=std/np.sqrt(n)
    )
    
    return pd.Series({
        'CI_Lower_95': ci_lower,
        'CI_Upper_95': ci_upper,
        'Mean': mean,
        'Std': std,
        'Count': n,
    })

# Apply to each group
ci_stats = df.groupby(['Year', 'Quarter', 'Parameter', 'Site ID']).apply(
    calculate_group_ci).unstack().reset_index()

#%%
# Create a dictionary for dropdown options
param_dropdown_opts = [
    {'label': p, 'value': c}
    for c, p in df[['Parameter Code', 'Parameter']].drop_duplicates().values
]


# Create year dropdown options
yr_dropdown_opts = [{'label': str(year), 'value': year} for year in sorted(df['Date'].dt.year.unique())]

# Create color mapping dict
site_colors = dict(zip(df["Site ID"].unique(), px.colors.qualitative.G10))

color_dict = {str(site): str(color) for site, color in zip(df["Site ID"].unique(), px.colors.qualitative.Safe)}

# 1. Sort the list of unique legend entries alphabetically or customly + cast to string
sorted_sites = [str(x) for x in sorted(df["Site ID"].unique())]

# Formatting parameters for dcc.RangeSlider
dateMin = df['Date'].min()
dateMax = df['Date'].max()


# Initial filter
i = 43502 # initial parameter code (set to 'Formaldehyde')
sample_df = (df.loc[df['Parameter Code'] == i].copy()).sort_values('Site ID') # param df for all yrs of data
sample_df["Site ID"] = sample_df["Site ID"].astype('string')
initial_param = sample_df['Parameter'].iloc[0]
initial_year = df['Date'].dt.year.max() # used to define 
initial_unit = sample_df['Units'].iloc[0]


initial_fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID",
                        color_discrete_map=color_dict,
                    #    / category_orders={color_dict: [str(x) for x in sorted(sample_df["Site ID"].unique())]},
                        title=f'{initial_param} - {initial_year}'
                         )

# Define size and style of scatter plot markers
initial_fig.update_traces(marker=dict(size=16,
                              line=dict(width=3,
                                        color='DarkSlateGrey')),
                  selector=dict(mode='markers'))


# Get the min and max dates for the filtered data
max_year = sample_df['Date'].dt.year.max()
initial_dateMin = pd.Timestamp(year=max_year, month=1, day=1) # sample_df['Date'].min()
initial_dateMax = sample_df['Date'].max()

# initial_fig.update_traces(mode="lines+markers")

initial_fig.update_layout(height=600)

initial_fig.update_xaxes(
    range=[initial_dateMin, initial_dateMax],
    autorange=False,
    rangeslider_visible=True,
    type='date'
)

initial_fig.update_yaxes(title_text= f"{initial_unit}")


# Calculate quarterly statistics for bar chart
sample_stats = quarterly_stats.loc[(quarterly_stats['Year']==initial_year) & (quarterly_stats['Parameter']==initial_param)].copy()

# Convert Site ID to string for proper display in the bar chart
sample_stats['Site ID'] = sample_stats['Site ID'].astype('string')

initial_fig_bar = px.bar(
    data_frame=sample_stats,  
    x="Quarter_Number", 
    y="Sample_Average",
    barmode='group',
    color="Site ID",
    color_discrete_map=color_dict,
    labels={'Sample_Average': 'Sample_Average'},
    height=400)
# initial_fig_bar.show()
# fig_bar = initial_fig_bar

#%%
# Initialize app with bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# App layout with two columns
app.layout = dbc.Container([
    dbc.Row([
        html.H1('Air Toxics Monitor - Processed Data', className='mb-4 mt-4') #mb = margin-bottom, mt = margin-top
    ]),
    
    # Row 2 - Controls, stats display, and scatter plot
    dbc.Row([
        # Left Column - Controls + Stats (matching scatter plot height)
        dbc.Col([
            html.Div([
                html.H5('Controls', className='mb-4'),
                
                html.Label('Select Parameter:', className='fw-bold'),
                dcc.Dropdown(
                    id='param-dropdown',
                    options=param_dropdown_opts, 
                    value=i, # initial param code
                    multi=False,
                    className='mb-3'
                ),
                
                html.Label('Select Year:', className='fw-bold'),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=yr_dropdown_opts, 
                    value=initial_year,
                    multi=False,
                    className='mb-4'
                ),
                
                html.Div(id='stats-display', 
                        className='p-2 bg-light rounded',
                        style={'flex': '1', 'overflowY': 'auto'}),
            ])
        ], width=2),
        
        # Right Column - Scatter Plot (height=500)
        dbc.Col([
            dcc.Graph(id='scatter-plot', figure=initial_fig, style={'height': '600px'}),
        ], width=9),
    ], className='g-1'), #mg=margin-bottom of size (4) 'mb-4'
    


    dbc.Row([
            # Left Column - Quarterly Stats (matching bar chart height)
            dbc.Col([
                html.Div([
                    html.H5('Quarterly Statistics', className='mb-4'),
                    html.Div(id='quarterly-stats-display', className='p-3 bg-light rounded', style={'flex': '1', 'overflowY': 'auto'}),
                ], style={'minHeight': '400px', 'display': 'flex', 'flexDirection': 'column'})
            ]), # , width=3
            
            # Right Column - Bar Chart (height=400)
            dbc.Col([
                dcc.Graph(id='bar-chart', figure=initial_fig_bar, style={'height': '400px'}),
            ]), # , width=9
        ], className='mb-4'),    


], fluid=True)

@callback(
    Output('scatter-plot', 'figure'), # component-id='scatter-plot' ; # component_property='figure'
    Output('stats-display', 'children'),
    Output('bar-chart', 'figure'),
    Output('quarterly-stats-display', 'children'), # Added for quarterly stats display
    Input('param-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_plot(selected_param_code, selected_year):
    # Filter by Parameter Code (which is what the dropdown returns)
    filtered_df = df[(df['Parameter Code'] == selected_param_code) & (df['Date'].dt.year == selected_year)]
    
    # Get the parameter name for display
    param_name = filtered_df['Parameter'].iloc[0] if len(filtered_df) > 0 else 'Unknown'
    param_units = filtered_df['Units'].iloc[0] if len(filtered_df) > 0 else 'Unknown'

    
    filtered_df['Site ID'] = filtered_df['Site ID'].astype(str) # Needed to correctly group the data into separate sites

    fig = px.scatter(
        data_frame=filtered_df, 
        x="Date", 
        y="Sample Value", 
        color="Site ID",
        color_discrete_map=color_dict,
        title=f'{param_name} - {selected_year}',
        labels={'Sample Value': 'Value'}
    )

    # Set x-axis range to the selected year
    year_start = pd.Timestamp(year=selected_year, month=1, day=1)
    year_end = pd.Timestamp(year=selected_year, month=12, day=31)
    
    fig.update_xaxes(
    range=[year_start, year_end],
    autorange=False,
    rangeslider_visible=True,
    type='date'
    )
    
    fig.update_yaxes(title_text=f'{param_units}')

    fig.update_layout(
        title={
            "text": f'24hr Average Samples - {selected_year} {param_name}',
            "font": {"weight": "bold"}, # Sets weight natively
            'x' : 0.5,
            "xanchor": 'center',
            "yref": "paper",
            "yanchor" : "bottom"
            
        },
        # margin=dict(t=180)
    )

    fig.update_traces(marker=dict(size=8,
                      line=dict(width=1,
                      color='DarkSlateGrey')),
                      selector=dict(mode='markers'))

    # Create stats display
    # TODO Update stats to show the specified year values
    stats = html.Div([
        html.P(f"Parameter: {param_name}", className='mb-2'),
        html.P(f"Year: {selected_year}", className='mb-2'),
        html.P(f"Total Samples: {len(filtered_df)}", className='mb-2'),
        html.P(f"Mean: {filtered_df['Sample Value'].mean():.2f}", className='mb-2'),
        html.P(f"Max: {filtered_df['Sample Value'].max():.2f}", className='mb-0'),
    ])
    
    # Add bar chart update
    bar_stats = quarterly_stats.loc[(quarterly_stats['Year']==selected_year) & 
                                     (quarterly_stats['Parameter']==param_name)].copy()
    bar_stats['Site ID'] = bar_stats['Site ID'].astype(str) # Needed to correctly group the data into separate sites
    


    fig_bar = px.bar(
        data_frame=bar_stats,  
        x="Quarter_Number", 
        y="Sample_Average",
        barmode='group',
        color="Site ID",
        color_discrete_map=color_dict,
        # title=f'{param_name} - Quarterly Average by Site',
        labels={'Sample_Average': 'Sample Average', 'Quarter_Number': 'Quarter'},
        height=400
    )

    fig_bar.update_layout(
        title={
            "text": f'{param_name} - Quarterly Average by Site',
            "font": {"weight": "bold"}, # Sets weight natively
            'x' : 0.5,
            "xanchor": 'center',
            "yref": "paper",
            "yanchor" : "bottom"
        },
    )

     # Create quarterly stats display
    if len(bar_stats) > 0:
        quarterly_mean = bar_stats['Sample_Average'].mean()
        quarterly_max = bar_stats['Sample_Average'].max()
        quarterly_count = bar_stats['Sample_Count'].sum()
        
        quarterly_stats_div = html.Div([
            html.P(f"Mean (Quarterly): {quarterly_mean:.2f}", className='mb-2'),
            html.P(f"Max (Quarterly): {quarterly_max:.2f}", className='mb-2'),
            html.P(f"Total Samples: {quarterly_count:.0f}", className='mb-0'),
        ])
    else:
        quarterly_stats_div = html.P("No data available", className='text-muted')

    return fig, stats, fig_bar, quarterly_stats_div


if __name__ == '__main__':
    app.run(debug=True)