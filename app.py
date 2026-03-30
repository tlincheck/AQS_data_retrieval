#import plotly.express as px
#import pandas as pd


from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import dash_ag_grid as dag
import pandas as pd
import datetime as dt


# Incorporate the data
#df_raw = pd.read_csv('merged_data_raw.csv', low_memory=False)
dfr = pd.read_excel('merged_data_raw.xlsx')

# Create a dictionary of key-value pairs for dropdown menu
df_dict = pd.Series(dfr['Parameter'].values, index=dfr['Parameter Code']).to_dict()
# Keys are Parameters, values are parameter codes

# --- Formatting the dictionary for the options property ---
# Use a list comprehension to create the required format:
# [{'label': 'New York City', 'value': 'NYC'}, ...]
dropdown_options = [{'label': v, 'value': k} for k, v in df_dict.items()]

# Formatting parameters for dcc.RangeSlider
dateMin = dfr['Date'].min()
dateMax = dfr['Date'].max()
yr_dropdown_opts = {str(year): int(year) for year in dfr['Date'].dt.year.unique()}




mark_values = dfr['Date'].dt.year.unique()
mark_dict = pd.Series(dfr['Date'].dt.year.unique(), index=dfr['Date'].dt.year.unique()).to_dict()
mark_opts = [{'label': v, 'value': k} for k, v in mark_dict.items()]

i = 43502
sample_df = dfr.loc[dfr['Parameter Code'] == i]
tm0 = (sample_df.loc[sample_df["Date"].dt.year == 2024]["Date"].min()).strftime('%Y-%m-%d')
tm1 = (sample_df.loc[sample_df["Date"].dt.year == 2024]["Date"].max()).strftime('%Y-%m-%d')

#sample_df["Date"] = sample_df["Date"].dt.strftime('%Y-%m-%d')


title1 = sample_df['Parameter'].iat[0]
dfr['Sample Value']

# x and y given as DataFrame columns
# df = px.data_df() # iris is a pandas DataFrame
fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID")
#fig.show()

# Initialize the app
app = Dash()

# App layout
app.layout = html.Div(children=[
    html.H1(children='Air Toxics Monitor Data App', style={'textAlign': 'center'}),

    # Dropdown component
    dcc.Dropdown(
        id='dropdown-menu',
        options = dropdown_options,
        value =43502,
        multi=False,
        ),

    dcc.Dropdown(
        id='yr-dropdown-menu',
        options = yr_dropdown_opts,
        value = list(yr_dropdown_opts.values())[-2],
        multi=False,
        ),

    # Container for dropdown container
    # html.Div(id='dropdown-output-container'),

    dcc.Graph(
        id='param-scatter-plot',
        figure={},
        style={'height': '80vh', 'width': '100%'} # Set height/width of the container
        ), #=fig),

    html.Div(id='range-slider-container'),


])

#sample_df.loc[sample_df["Date"].dt.year == 2024]["Date"].max()
@callback(
    Output(component_id='param-scatter-plot', component_property='figure'),
    Input(component_id='dropdown-menu', component_property='value'), 
    Input(component_id='yr-dropdown-menu', component_property='value'),
)

def update_graph(pollutant_selection, yr_selection):
    # Retrieve df for selected parameter
    pollutant_df = dfr.loc[dfr['Parameter Code'] == pollutant_selection]
    pollutant_df["Site ID"] = pollutant_df["Site ID"].astype(str) # Convert Site IDs to string type for discrete 
    
    yr = str(yr_selection)

    # Retrieve name of selected parameter 
    param_name = pollutant_df['Parameter'].iat[0]
    
    fig = px.scatter(data_frame=pollutant_df, x="Date", y="Sample Value", 
        color="Site ID", 
        symbol="Site ID",
        hover_data= "Qualifier - 1",
        title=f'{param_name}') # sample_df['Parameter'].iat[0]
    
    #fig.update_layout(xaxis_range=[1, 10], overwrite=True),
    fig.update_xaxes(range=[f'{yr}-01-01', f'{yr}-12-31'], autorange=False, rangeslider_visible=True),
                     #range=[timestamp1,timestamp2])
    return fig


# range=[f"{yr0}-01-01", f"{yr0}-12-31"]


# Run the app
if __name__ == '__main__':
    app.run(debug=True)

# -----------------------------------------------------------------------

# Import and clean dat (importing into pandas)
#df = pd.read_excel()


'''


# Range slider for graph
    dcc.RangeSlider(
        id='range-slider',
        min= dfr['Date'].min().year, # min value available for selection; dfr['Date'].min()
        max= dfr['Date'].max().year,# dateMax, # max value available for selection
        step=1, # defines points for RangeSlider between min and max
        value=[2021, 2025], #dfr['Date'].dt.year,
        marks= {str(year): str(year) for year in dfr['Date'].dt.year.unique()}, #{date.day:date.day for date in dfr['Date'].dt.date.unique()},#mark_dict, # {str(year): str(year) for year in dfr['Date'].dt.year.unique()}
        tooltip={'placement':'bottom', 'always_visible': True},
    )

    # pollutant_df["Date"] = pollutant_df["Date"].dt.strftime('%Y-%m-%d')

    #yr0= pollutant_df.loc[pollutant_df["Date"].dt.year == yr_selection]["Date"].min().strftime('%Y-%m-%d')
    #yr1 = pollutant_df.loc[pollutant_df["Date"].dt.year == (yr_selection+1)]["Date"].min().strftime('%Y-%m-%d')

    
fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )





    # Range slider for graph
    dcc.RangeSlider(
        id='range-slider'
        min=dateMin, # min value available for selection; dfr['Date'].min()
        max=dateMax, # max value available for selection
        value=[2021, 2025],
        mark_values=mark_dict,
        step=1, # defines points for RangeSlider between min and max
        tooltip={'placement':'bottom', 'always_visible': True},
    )
'''

'''
    # data table component in app layout
    dag.AgGrid(
        rowData=dfr.to_dict('records'),
        columnDefs=[{"field":i} for i in dfr.columns]
    )
    '''

'''
def sample_df(param):
    sample_df = dfr.loc[dfr['Parameter Code'] == param]
    code = dfr.loc[dfr['Parameter'] == 'Formaldehyde','Parameter Code'].iloc[0]
    # ttle = sample_df['Parameter'].iat[0]
    fig = px.scatter(
        data_frame=sample_df,
        x="Date",
        y="Sample Value", 
        color="Site ID", 
        symbol="Site ID", 
        title= "Title of plot") # sample_df['Parameter'].iat[0]
    fig.update_coloraxes(showscale=False) # If it's a colorbar
    fig.update_xaxes(rangeslider_visible=True)
        fig.update_layout(title="New Title")
    return fig


    # pollutant_name = dfr.loc[dfr['Parameter code'] == pollutant_selection, 'Parameter'].iloc[0]
    # dfr.loc[dfr['Parameter Code'] == 43502, 'Parameter'].iloc[0]
    # ttle = sample_df['Parameter'].iat[0]
'''

'''
@callback(
    Output('dropdown-output-container', 'children'),
    Input('dropdown', 'value')
)
def update_output(chosen_parameter):
    return f'You have selected {chosen_parameter}'
    '''