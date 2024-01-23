import dash
import pandas as pd
import plotly.express as px
import dash_mantine_components as dmc
from dash import Dash, dash_table, dcc, callback, Output, Input, html

# Load data
df = pd.read_csv('Updated_Ireland_data.csv')
df['Engine_power'] = df['Engine_power'].astype(int)

external_stylesheets = [dmc.theme.DEFAULT_COLORS]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Common Styling
common_col_style = {'padding': '10px', 'border': '1px solid', 'margin-bottom': '8px'}
common_text_style = {'font-size': '20px', 'padding': '10px'}
common_slider_style = {'padding': '10px', 'padding-top': '0px'}
common_graph_style = {'border': '1px dashed', 'background-color': '#FFA351', 'padding': '10px'}
common_title_style = {'margin-bottom': '15px', 'text-decoration': 'underline'}

app.layout = dmc.Container([
    dmc.Title('Monitoring of CO2 emissions', size="h1", align='center', style=common_title_style),
    dmc.Grid([
        dmc.Col([
            dmc.Text("Select EU Manufacturer", style={'margin-bottom': '5px', 'fontWeight': 'bold'}, size="lg"),
            dmc.MultiSelect(
                id='manufacture-dropdown',
                data=sorted([{'value': make, 'label': make} for make in df['Manuf_name_EU'].unique()],
                            key=lambda x: x['label']),
                value=sorted(df['Manuf_name_EU'].value_counts().index),
                placeholder="Select Manufacturer",
            ),
        ], span=12, style={**common_col_style, 'background-color': '#FFA351'}),
        dmc.Col([
            dmc.Text("Table", size="lg", mb=5, align='center', mt=5, style={'border': '1px dashed'}),
            dash_table.DataTable(id='main-table',
                                 columns=[{'name': col, 'id': col} for col in df.columns],
                                 style_table={'overflowX': 'auto', 'margin-bottom': '10px'},
                                 page_size=10),
        ], span=8, style={**common_col_style, 'border': '1px dashed', 'padding': '10px', 'background-color': '#FFA351'}),
        dmc.Col([
            dmc.Text("Fuel Type", size="lg", style=common_text_style),
            dcc.RadioItems(
                id='fuel-type-radio',
                options=[{'value': fuel_type, 'label': fuel_type} for fuel_type in df['Fuel_type'].unique()],
                value=df['Fuel_type'].unique()[0],
                labelStyle={'display': 'block', 'padding': '10px'},
            ),
            dmc.Text("Fuel Consumption", size="lg", style={**common_text_style, 'padding-bottom': '2px'}),
            dmc.Slider(
                id="fuel-slider",
                min=df['Fuel_consumption'].min(),
                max=df['Fuel_consumption'].max(),
                step=1,
                style=common_slider_style,
                showLabelOnHover=True,
                value=df['Fuel_consumption'].max() / 2,
            ),
            dmc.Text("Engine Power", size="lg", style={**common_text_style, 'padding-bottom': '2px'}),
            dmc.Slider(
                id="engine-power-slider",
                min=df['Engine_power'].min(),
                max=df['Engine_power'].max(),
                step=1,
                style=common_slider_style,
                showLabelOnHover=True,
                value=df['Engine_power'].max() / 2,
            ),
            dmc.Text("Engine Capacity", size="lg", style={**common_text_style, 'padding-bottom': '2px'}),
            dmc.Slider(
                id="engine-capacity-slider",
                min=df['Engine_capacity'].min(),
                max=df['Engine_capacity'].max(),
                style=common_slider_style,
                step=1,
                showLabelOnHover=True,
                value=df['Engine_capacity'].max() / 2,
            ),
        ], span=4, style={**common_col_style, 'font-weight': 'bold'}),
        dmc.Col([
            dcc.Graph(id='Manuf_name_EU_histogram', style=common_graph_style),
        ], span=8, style={**common_col_style}),
        dmc.Col([
            dcc.Graph(id='Fuel_type_histogram', style={**common_graph_style, 'margin': '5px'}),
        ], span=4, style={**common_col_style}),
        dmc.Col([
            dcc.Graph(id='Engine_scatter', style={**common_graph_style, 'width': '45%', 'padding': '30px'}),
            dcc.Graph(id='fc_mass_scatter', style={**common_graph_style, 'width': '45%', 'padding': '30px'}),
        ], span=12, style={'display': 'flex', 'justify-content': 'space-around', 'padding': '10px'})
    ]),
], style={'background-color': '#FFBE7B'}, fluid=True)

@callback(
    [Output('main-table', 'data'),
     Output('Manuf_name_EU_histogram', 'figure'),
     Output('Fuel_type_histogram', 'figure'),
     Output('Engine_scatter', 'figure'),
     Output('fc_mass_scatter', 'figure')],
    [Input('fuel-type-radio', 'value'),
     Input('manufacture-dropdown', 'value'),
     Input('fuel-slider', 'value'),
     Input('engine-power-slider', 'value'),
     Input('engine-capacity-slider', 'value')]
)
def update_data(selected_fuel_type, manufacture_values, selected_fuel, selected_engine_power, selected_engine_capacity):
    if not isinstance(selected_fuel_type, list):
        selected_fuel_type = [selected_fuel_type]

    # Filter DataFrame based on user inputs
    filtered_df = df[df['Manuf_name_EU'].isin(manufacture_values) & df['Fuel_type'].isin(selected_fuel_type) & (df['Fuel_consumption'] < selected_fuel) 
                     & (df['Engine_power'] < selected_engine_power)
                     & (df['Engine_capacity'] < selected_engine_capacity)]

    table_data = filtered_df.to_dict('records')

    # Plotting CO2 Emission Statistics by EU Manufacturer
    eu_manuf_stats = filtered_df.groupby('Manuf_name_EU')['EWLTP'].agg(['mean']).reset_index()
    eu_manuf_stats = eu_manuf_stats.sort_values(by='mean', ascending=False)
    eu_manuf_stats = pd.melt(eu_manuf_stats, id_vars='Manuf_name_EU', value_vars=['mean'], var_name='Statistic')
    eu_manuf_stats_fig = px.bar(eu_manuf_stats,
                                x='Manuf_name_EU',
                                y='value',
                                color='Manuf_name_EU',
                                title='CO2 Emission Statistics by EU Manufacturer',
                                labels={'value': 'CO2 Emission (g/km)'},
                                height=500,
                                color_discrete_sequence=px.colors.qualitative.Plotly)

    # Plotting Average EWLTP by Fuel Type
    fuel_type_filtered_df = df[df['Manuf_name_EU'].isin(manufacture_values) & (df['Fuel_consumption'] < selected_fuel)
                     & (df['Engine_power'] < selected_engine_power)
                     & (df['Engine_capacity'] < selected_engine_capacity)]
    fuel_type_mean = fuel_type_filtered_df.groupby('Fuel_type')['EWLTP'].mean().reset_index()
    fuel_type_mean = fuel_type_mean.round(1).sort_values('EWLTP')
    fig_fuel_type_mean_fig = px.bar(fuel_type_mean, x='Fuel_type', y='EWLTP',
                                    title='Average EWLTP by Fuel Type',
                                    labels={'EWLTP': 'Average EWLTP'},
                                    color='Fuel_type',
                                    text='EWLTP',
                                    color_discrete_sequence=px.colors.qualitative.Plotly).update_layout(showlegend=False)

    # Scatter Plot of Engine Capacity and Engine Power
    capacity_mass_plot = px.scatter(filtered_df, x="Engine_power", y="Engine_capacity", color='EWLTP', size='EWLTP',
                                    title='Engine Capacity and Engine Power',
                                    labels={'EWLTP': 'CO2 Emission (g/km)', 'Engine_power': 'Engine Power', 'Engine_capacity': 'Engine Capacity'},
                                    color_continuous_scale=px.colors.sequential.Viridis)

    # Scatter Plot of Mass vs Fuel Consumption
    fc_mass_scatter = px.scatter(filtered_df, x='Mass_running_order', y='Fuel_consumption', color='EWLTP', size='EWLTP',
                                title='Scatter Plot of Mass vs Fuel Consumption',
                                labels={'EWLTP': 'CO2 Emission (g/km)', 'Mass_running_order': 'Mass', 'Fuel_consumption': 'Fuel Consumption'},
                                color_continuous_scale=px.colors.sequential.Viridis)

    return table_data, eu_manuf_stats_fig, fig_fuel_type_mean_fig, capacity_mass_plot, fc_mass_scatter

if __name__ == '__main__':
    app.run_server(debug=True)