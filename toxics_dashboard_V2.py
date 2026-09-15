from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
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
    Sample_Count=('Sample Value', 'count')
).reset_index() 

# Remove commas from MAAC columns for casting to float() 
df['MAAC ppb'] = df['MAAC ppb'].str.replace(',', '', regex=False)
df['MAAC ug/m3'] = df['MAAC ug/m3'].str.replace(',', '', regex=False)

#%%
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

# Formatting parameters for dcc.RangeSlider
dateMin = df['Date'].min()
dateMax = df['Date'].max()


# Create color mapping dict
color_dict = {str(site): str(color) for site, color in zip(df["Site ID"].unique(), px.colors.qualitative.T10)} #G10, D3, Safe

# 1. Sort the list of unique legend entries alphabetically or customly + cast to string
# sorted_sites = [str(x) for x in sorted(df["Site ID"].unique())]

# Create units dict
units_opts = [{'label': unit, 'value': unit} for unit in df['Units'].unique()]

# Initial filter
i = 43502 # initial parameter code (set to 'Formaldehyde')
sample_df = df.loc[df['Parameter Code'] == i].copy() # param df for all yrs of data
initial_param = sample_df['Parameter'].iloc[0]
sample_df["Site ID"] = sample_df["Site ID"].astype('string') # Cast to string for categorical plotting
initial_year = df['Date'].dt.year.max() # used to define 
initial_unit = sample_df['Units'].iloc[0]




# Function to retrieve MAAC values for plotting
def get_MAAC(data): # Input is dataframe for current parameter being plotted on scatterplot
                    # Input: sample_df

    unit = data['Units'].iloc[0] # Retrieve units column in df - save 1st value

    if 'parts per billion' in unit.lower():
        maac_value = float(data['MAAC ppb'].iloc[0])
    elif 'micrograms' in unit.lower():
        maac_value = float(data['MAAC ug/m3'].iloc[0])
    elif 'nanogram' in unit.lower():
        maac_value = float(data['MAAC ug/m3'].iloc[0]) * 1000 # Convert MAAC value to nanograms
    else:
        maac_value = None

    return maac_value, unit

maac, param_unit = get_MAAC(sample_df) # Returns MAAC value and parameter unit


initial_fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID", color_discrete_map=color_dict,
                         title=f'{initial_param} - {initial_year}') #title=f'{initial_param} - {initial_year}'

# Get the min and max dates for the filtered data
max_year = sample_df['Date'].dt.year.max()
initial_dateMin = pd.Timestamp(year=max_year, month=1, day=1) # sample_df['Date'].min()
initial_dateMax = sample_df['Date'].max()

# initial_fig.update_traces(mode="lines+markers")

# Add MAAC as hline to scatterplot
if maac is not None:
    initial_fig.add_trace(
        go.Scatter(
            x=[initial_dateMin, initial_dateMax],
            y=[maac, maac],
            mode="lines",
            line=dict(color="green", width=2, dash="dash"),
            name="MAAC",
            showlegend=True,       # Displays "MAAC" in your legend
            hoverinfo="skip"       # Prevents data popups if you hover over the line
        )
    )


# initial_fig.update_layout() # height=600 # title_automargin=True

initial_fig.update_xaxes(
    range=[initial_dateMin, initial_dateMax],
    autorange=False,
    rangeslider_visible=True,
    type='date'
)

#Update y-axes labels
initial_fig.update_yaxes(title_text= f"{initial_unit}", fixedrange=False)



# Calculate quarterly statistics for bar chart
sample_stats = quarterly_stats.loc[(quarterly_stats['Year']==initial_year) & (quarterly_stats['Parameter']==initial_param)].copy()

# Convert Site ID to string for proper display in the bar chart
sample_stats['Site ID'] = sample_stats['Site ID'].astype(str)

initial_fig_bar = px.bar(
    data_frame=sample_stats,  
    x="Quarter_Number", 
    y="Sample_Average",
    barmode='group',
    color="Site ID",
    color_discrete_map=color_dict,
    title=f'{initial_param} - Quarterly Average by Site',
    labels={'Sample_Average': 'Sample_Average'},
    ) # height=400
# initial_fig_bar.show()
# fig_bar = initial_fig_bar


# Merge dataframes to obtain units


#%%
# Initialize app with bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# App layout with two columns
app.layout = dbc.Container([
    # Row 1 - Header
    dbc.Row([
        html.H1('Air Toxics Monitor - Processed Data', className='mb-4 mt-4') #mb = margin-bottom, mt = margin-top
    ]),
    
    # Row 2 - Controls and Dropdowns
    dbc.Row([
        # Left Column - Select Parameter Dropdown
        dbc.Col([
            html.Div([
                # html.H5('Controls', className='mb-4'),
                html.Label('Select Parameter:', className='fw-bold'),
                dcc.Dropdown(
                    id='param-dropdown',
                    options=param_dropdown_opts, 
                    value=i, # initial param code
                    multi=False,
                    className='mb-4',
                ),

                dcc.Checklist(
                    id='threshold-toggle',
                    options=[{'label': ' Show MAAC Threshold Line', 'value': 'show'}],
                    value=[],  # Empty list sets default state to UNCHECKED (off)
                    className='fw-bold text-success mt-2'
                ),       
            ]),
        ], width=6), # width=6

        # Right Column - Select Year Dropdown
        dbc.Col([
                html.Label('Select Year:', className='fw-bold'),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=yr_dropdown_opts, 
                    value=initial_year,
                    multi=False,
                    className='mb-4',
                ),
        # ], width=6),  

         # NEW ELEMENT: Toggle switch component for threshold overlays
        # dcc.Checklist(
        #     id='threshold-toggle',
        #     options=[{'label': ' Show MAAC Threshold Line', 'value': 'show'}],
        #     value=[],  # Empty list sets default state to UNCHECKED (off)
        #     className='fw-bold text-success'
        #     ),
        ], width=6),


    ], className='mb-4'),
    
    # Row 3 - Plots
    dbc.Row([   
        #Left Column - Scatter Plot (height=500)
        dbc.Col([
            dcc.Graph(id='scatter-plot', figure=initial_fig, style={'height': '400px'}),
        ], width=7), 

        # Right Column - Bar Chart (height=400)
        dbc.Col([
            dcc.Graph(id='bar-chart', figure=initial_fig_bar, style={'height': '400px'}),
        ], width=5),

        

    ], className='mb-4'), #mg=margin-bottom of size (4)

    # Row 4 - Stats & Data Table
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5('Statistics', className='mb-4'),
                html.Div(id='quarterly-stats-display', 
                    className='p-3 bg-light rounded',
                    style={'flex': '1', 'overflowY': 'auto'}),
            ], style={'minHeight': '500px', 'display': 'flex', 'flexDirection': 'column'})
        ], width=3),
    ], className='mb-4')
], fluid=True)
                



@callback(
    Output('scatter-plot', 'figure'), # component-id='scatter-plot' ; # component_property='figure'
    #  Output('stats-display', 'children'),
    Output('bar-chart', 'figure'),
    Output('quarterly-stats-display', 'children'), # Added for quarterly stats display
    Input('param-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    Input('threshold-toggle', 'value') # NEW INPUT DETECTOR for MAAC checkbox
)
def update_plot(selected_param_code, selected_year, toggle_value):
    # Filter by Parameter Code (which is what the dropdown returns)
    filtered_df = df[(df['Parameter Code'] == selected_param_code) & (df['Date'].dt.year == selected_year)]
    
    ci = filtered_df.groupby(['Year', 'Quarter', 'Parameter', 'Site ID']).apply(
    calculate_group_ci).unstack().reset_index()
    # filtered_ci_stats = .loc[(ci_stats["Parameter"]==param_name) & (ci_stats["Year"]==selected_year)]
    
    # Get the parameter name for display
    param_name = filtered_df['Parameter'].iloc[0] if len(filtered_df) > 0 else 'Unknown'
    param_units = filtered_df['Units'].iloc[0] if len(filtered_df) > 0 else 'Unknown'
    
    maac, param_unit = get_MAAC(filtered_df) # Returns MAAC value and parameter unit

    # Cast Site ID to string
    filtered_df['Site ID'] = filtered_df['Site ID'].astype(str) # Needed to correctly group the data into separate sites

    # Initialize the base scatter figure
    fig = px.scatter(
        data_frame=filtered_df, 
        x="Date", 
        y="Sample Value", 
        color="Site ID",
        color_discrete_map=color_dict,
        # title=f'{param_name} - {selected_year}',
        labels={'Sample Value': 'Value'}
    )
# 
    # Set x-axis range to the selected year
    year_start = pd.Timestamp(year=selected_year, month=1, day=1)
    year_end = pd.Timestamp(year=selected_year, month=12, day=31)

    # Add MAAC value to scatter plot
    if maac is not None and 'show' in toggle_value:
        # initial_fig.add_hline(y=maac, xref="paper") # , line_color='green', line_dash='dash', line_width=2#, label=f'MAAC ({param_unit}): {maac:.2f}'
        fig.add_trace(
            go.Scatter(
                x=[year_start, year_end],
                y=[maac, maac],
                mode="lines",
                line=dict(color='green', width=2, dash='dash'),
                name="MAAC",
                showlegend=True,
                hoverinfo="skip",
                xaxis="x",   # Protects against layout drops
                yaxis="y"    # Protects against layout drops
            )
        )

    fig.update_xaxes(
    range=[year_start, year_end],
    autorange=False,
    rangeslider_visible=True,
    type='date'
    )
    
    fig.update_layout(
        title={
            "text": f'{param_name}:{selected_year} 24hr Average Samples',
            'x' : 0.5,
            "xanchor": 'center',
            "yref": "paper",
            "yanchor" : "bottom"
        },
        # margin=dict(t=180)
    )

    fig.update_yaxes(title_text=f'{param_units}', fixedrange=False)

    # Create stats display
    # TODO Update stats to show the specified year values
    # stats = html.Div([
    #     html.P(f"Parameter: {param_name}", className='mb-2'),
    #     html.P(f"Year: {selected_year}", className='mb-2'),
    #     html.P(f"Total Samples: {len(filtered_df)}", className='mb-2'),
    #     html.P(f"Mean: {filtered_df['Sample Value'].mean():.2f}", className='mb-2'),
    #     html.P(f"Max: {filtered_df['Sample Value'].max():.2f}", className='mb-0'),
    # ])
    
    # Add bar chart update
    bar_stats = quarterly_stats.loc[(quarterly_stats['Year']==selected_year) & 
                                     (quarterly_stats['Parameter']==param_name)].copy()
    bar_stats['Site ID'] = bar_stats['Site ID'].astype(str) # Needed to correctly group the data into separate sites

    # ci_stats.loc[(ci_stats["Parameter"]==param_name) & (ci_stats["Year"]==selected_year)]

    if len(filtered_df) > 0:
            # 1. Generate confidence intervals
            ci_raw = filtered_df.groupby(['Year', 'Quarter', 'Parameter', 'Site ID']).apply(calculate_group_ci)
            
            # 2. Flatten the MultiIndex
            ci = ci_raw.reset_index()
            
            # Safely convert to string for the merge operation
            ci['Site ID'] = ci['Site ID'].astype(str) 
            
            # CRITICAL FIX: Extract the raw integer quarter (1-4) from the Period object
            # This aligns it perfectly with your bar_stats['Quarter_Number'] data type
            ci['Quarter_Int'] = ci['Quarter'].dt.quarter
            
            # 3. Calculate explicit delta error lengths (whisker extensions)
            ci['error_upper_delta'] = ci["CI_Upper_95"] - ci["Mean"]
            ci['error_lower_delta'] = ci["Mean"] - ci["CI_Lower_95"]
            
            # 4. Merge seamlessly using the newly matched integer keys
            bar_stats = bar_stats.merge(
                ci[['Quarter_Int', 'Site ID', 'error_upper_delta', 'error_lower_delta']], 
                left_on=['Quarter_Number', 'Site ID'], 
                right_on=['Quarter_Int', 'Site ID'], 
                how='left'
        )
    else:
        # Fallback empty columns to prevent crashing if no data matches
        bar_stats['error_upper_delta'] = None
        bar_stats['error_lower_delta'] = None


    fig_bar = px.bar(
        data_frame=bar_stats,  
        x="Quarter_Number", 
        y="Sample_Average",
        error_y="error_upper_delta",      # Point directly to the row-aligned column
        error_y_minus="error_lower_delta",  # Point directly to the row-aligned column
        barmode='group',
        color="Site ID",
        color_discrete_map=color_dict,
        # title=f'{param_name} - Quarterly Average by Site',
        labels={'Sample_Average': 'Sample Average', 'Quarter_Number': 'Quarter'},
        height=400
    )

    # Style error bar styling cleanly (adds cap width)
    fig_bar.update_traces(error_y=dict(thickness=1.5, width=4, color='black'))

    # Add MAAC threshold line to bar chart
    if maac is not None and 'show' in toggle_value:
            fig_bar.add_trace(
                go.Scatter(
                    x=[1, 4],            # Spans from Quarter 1 to Quarter 4
                    y=[maac, maac],      # Draws flat line at the MAAC threshold
                    mode="lines",
                    line=dict(color='green', width=2, dash='dash'),
                    name="MAAC",
                    showlegend=False,    # Hidden here so you don't duplicate the legend entry
                    hoverinfo="skip",    # Keeps bar hovers clean
                    xaxis="x",
                    yaxis="y"
                )
            )

    fig_bar.update_layout(
        title={
            "text": f'{param_name} - Quarterly Average by Site',
            'x' : 0.5,
            "xanchor": 'center',
            "yref": "paper",
            "yanchor" : "bottom"
        },
        # margin=dict(t=180)
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

    return fig, fig_bar, quarterly_stats_div # stats,


if __name__ == '__main__':
    app.run(debug=True)