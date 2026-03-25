#import plotly.express as px
#import pandas as pd


from dash import Dash, dcc, html, callback, Output, Input
import plotly.express as px
import dash_ag_grid as dag
import pandas as pd


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

# mark_values = dfr['Date'].dt.year.unique()

i = 43502
sample_df = dfr.loc[dfr['Parameter Code'] == i]

title = sample_df['Parameter'].iat[0]
dfr['Sample Value']

# x and y given as DataFrame columns
# df = px.data_df() # iris is a pandas DataFrame
fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID", title="Parameter")


# Initialize the app
app = Dash()

# App layout
app.layout = html.Div(children=[
    html.H4(children='My first App with Data - new updated text'),

    # ADD DROPDOWN component here?
    dcc.Dropdown(
        #options=['Option 1', 'Option 2', 'Option 3'],
        options = dropdown_options,
        value='43502', id='dropdown'),

    html.Div(id='dropdown-output-container'),

    dcc.Graph(
        id='param-scatter-plot',
        figure={}), #=fig),

    # table slider
    dcc.RangeSlider(
        min=dateMin,
        max=dateMax,
        step=None,
        id='range-slider'
    )

    # data table component
    dag.AgGrid(
        rowData=dfr.to_dict('records'),
        columnDefs=[{"field":i} for i in dfr.columns]
    )
    
])

@callback(
    Output('dropdown-output-container', 'children'),
    Input('dropdown', 'value')
)
def update_output(chosen_parameter):
    return f'You have selected {chosen_parameter}'


@callback(
    Output(component_id='param-scatter-plot', component_property='figure'),
    Input(component_id='dropdown', component_property='value')
)
def sample_df(param):
    sample_df = dfr.loc[dfr['Parameter Code'] == param]
    fig = px.scatter(
        data_frame=sample_df,
        x="Date",
        y="Sample Value", 
        color="Site ID", 
        symbol="Site ID", 
        title="Parameter")
    fig.update_coloraxes(showscale=False) # If it's a colorbar
    return fig



# Run the app
if __name__ == '__main__':
    app.run(debug=True)

# -----------------------------------------------------------------------

# Import and clean dat (importing into pandas)
#df = pd.read_excel()

