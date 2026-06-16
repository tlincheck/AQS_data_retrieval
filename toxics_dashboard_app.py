#%%
from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd

# Incorporate the data
df = pd.read_csv('merged_data_processed.csv')
df['Date'] = pd.to_datetime(df['Date'])


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


# Initial filter
i = 43502 # initial parameter code (set to 'Formaldehyde')
sample_df = df.loc[df['Parameter Code'] == i].copy() # param df for all yrs of data
initial_param = sample_df['Parameter'].iloc[0]
initial_year = df['Date'].dt.year.max() # used to define 


initial_fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID", 
                         title=f'{initial_param} - {initial_year}')

# Get the min and max dates for the filtered data
max_year = sample_df['Date'].dt.year.max()
initial_dateMin = pd.Timestamp(year=max_year, month=1, day=1) # sample_df['Date'].min()
initial_dateMax = sample_df['Date'].max()

# initial_fig.update_traces(mode="lines+markers")

initial_fig.update_xaxes(
    range=[initial_dateMin, initial_dateMax],
    autorange=False,
    rangeslider_visible=True,
    type='date'
)


fig = initial_fig


#%%
# Initialize app with bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# App layout with two columns
app.layout = dbc.Container([
    dbc.Row([
        html.H1('Air Toxics Monitor - Processed Data', className='mb-4 mt-4')
    ]),
    
    dbc.Row([
        # Left Column - Controls
        dbc.Col([
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
            
            html.Div(id='stats-display', className='p-3 bg-light rounded'),
            
        ], width=3),
        
        # Right Column - Plot
        dbc.Col([
            dcc.Graph(id='scatter-plot', figure=initial_fig),
        ], width=9),
    ], className='mb-4'),
    
], fluid=True)

@callback(
    Output('scatter-plot', 'figure'),
    Output('stats-display', 'children'),
    Input('param-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_plot(selected_param_code, selected_year):
    # Filter by Parameter Code (which is what the dropdown returns)
    filtered_df = df[(df['Parameter Code'] == selected_param_code) & (df['Date'].dt.year == selected_year)]
    
    # Get the parameter name for display
    param_name = filtered_df['Parameter'].iloc[0] if len(filtered_df) > 0 else 'Unknown'
    
    fig = px.scatter(
        data_frame=filtered_df, 
        x="Date", 
        y="Sample Value", 
        color="Site ID",
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
    
    # Create stats display
    # TODO Update stats to show the specified year values
    stats = html.Div([
        html.P(f"Parameter: {param_name}", className='mb-2'),
        html.P(f"Year: {selected_year}", className='mb-2'),
        html.P(f"Total Samples: {len(filtered_df)}", className='mb-2'),
        html.P(f"Mean: {filtered_df['Sample Value'].mean():.2f}", className='mb-2'),
        html.P(f"Max: {filtered_df['Sample Value'].max():.2f}", className='mb-0'),
    ])
    
    return fig, stats

if __name__ == '__main__':
    app.run(debug=True)