# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 21:56:41 2020

@author: Tri
"""

# Import required libraries
import dash
import pathlib
import dash_core_components as dcc
import dash_html_components as html
import hydrofunctions as hf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction
from datetime import datetime


# get relative data folder
PATH = pathlib.Path("__file__").parent
DATA_PATH = PATH.joinpath("Data").resolve()

# Path to Data File
Bacteria_Data = pd.read_csv(DATA_PATH.joinpath("OWS_BacteriaData_2018.csv"))
Station_Data = pd.read_csv(DATA_PATH.joinpath("Station_Data.csv"))
USGS_Data = pd.read_csv(DATA_PATH.joinpath("USGS_Gauges.csv"))

###############################################################################
# Mapbox Token                                                                #
###############################################################################
mapbox_access_token = "pk.eyJ1IjoicGhhbTk1IiwiYSI6ImNrNnB5aDMwZTFwYmwzbG83NmFvYXdncTgifQ.SGeZeoKIsPalUdyPzARNEg"

###############################################################################
# Setting the dashboard                                                       #
###############################################################################
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server
###############################################################################
# Create app layout                                                           #
###############################################################################
app.layout = html.Div(
    [
        dcc.Store(id = "aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id = "output-clientside"),
        #######################################################################
        # Top Row Setup
        # Title and 'Visit Us' button
        #######################################################################
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src = app.get_asset_url("pikachu.jpg"),
                            id = "OklahomaWaterSurvey-image",
                            style = {
                                "height": "80px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className = "one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Oklahoma Stream Data",
                                    style = {"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "", style = {"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Visit Us", id = "learn-more-button"),
                            href="http://www.ou.edu/okh2o",
                        )
                    ],
                    className = "one-third column",
                    id = "button",
                ),
            ],
            id = "header",
            className = "row flex-display",
            style={"margin-bottom": "25px"},
        ),
        #######################################################################
        # Second Row
        # Oklahoma Map and Streamflow Options
        #######################################################################
        html.Div(
            [
                html.Div(
                    id="StationMap_Container",
                    children=[
   
                        dcc.Graph(
                            id="station_map",
                            figure={
                            },
                            config={"scrollZoom": True, "displayModeBar": True},
                        ),
                        dcc.RadioItems(
                             id="mapbox-view-selector",
                             options=[
                                {"label": "outdoors", "value": "outdoors"},
                                {"label": "satellite", "value": "satellite"},
                                {"label": "satellite-street",
                                 "value": "mapbox://styles/mapbox/satellite-streets-v9",
                                },
                            ],
                            value="outdoors",
                            labelStyle={'display': 'inline-block'},
                        ),
                ],
                   # [dcc.Graph(id="Oklahoma_Map")],
                className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="TimeSeries")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        #######################################################################
        # Third Row
        # Oklahoma Streamflow Probability of Exceedance
        # E.Coli Plots
        #######################################################################
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="Bacteria_Avg")],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [dcc.Graph(id="FlowDuration")],
                    className="pretty_container six columns",
                ),
                html.Div(id='intermediate-value', style={'display': 'none'})
            ],
            className="row flex-display",
        ),

    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

###############################################################################
# Main figure map with gauge and sampling locations                           #
###############################################################################
@app.callback(
    Output("station_map", "figure"),
    [Input("mapbox-view-selector", "value"),],
)
def Make_Station_Map(style):
    # Setting up the layout
    layout = dict(
            clickmode="event+select",
            autosize = True,
            automargin = True,
            margin = dict(l = 30, r = 30, b = 20, t = 40),
            hovermode = "closest",
            plot_bgcolor = "#F9F9F9",
            paper_bgcolor = "#F9F9F9",
            #legend = dict(font = dict(size = 10), orientation = "h"),
            showlegend = False,
            title = "State of Oklahoma",
            mapbox = dict(
                    accesstoken = mapbox_access_token,
                    style = style,
                    center = dict(lat=35.2226, lon=-97.4395),
                    zoom = 5,
                    pitch=0,
                    ),
            )
    
    data =[]
    # Adding Bacterial Sampling Locations
    ows_trace = go.Scattermapbox(
        lat=Bacteria_Data["Lat"].tolist(),
        lon=Bacteria_Data["Long"].tolist(),
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=7,
            color='blue',
            opacity=0.7
        ),
        text=Bacteria_Data["Station_Name"].tolist(),
        #name = 'Bacteria Sampling',
        hoverinfo='text'
    )
    data.append(ows_trace)
    # Adding USGS Stations
    usgs_trace = go.Scattermapbox(
        lat=USGS_Data["Lat"].tolist(),
        lon=USGS_Data["Long"].tolist(),
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=7,
            color='red',
            opacity=0.7
        ),
        text=USGS_Data["Station_Name"].tolist(),
        #name = 'Gauge',
        hoverinfo='text'
    )
    data.append(usgs_trace)
    
    
    
    # Return Dict for Figure
    figure = {"data": data, 'layout':layout}    
    return figure

###############################################################################
# Callback to Time Series Plot                                                #
###############################################################################
@app.callback(
    Output("TimeSeries", "figure"),
    [Input("station_map", "hoverData"),
     ],
)
def Make_TimeSeries_Plot(Selected_Station):
    
    
    # Find which one has been triggered
    ctx = dash.callback_context 
    station_id = ""
    station_type = ""
    
    if ctx.triggered:
        splitted = ctx.triggered[0]["prop_id"].split(".")
        station_id = splitted[0]
        station_type = splitted[1]
    
    
    # If Point is Clicked and is on the Map:
    if station_id == "station_map" and station_type == "hoverData":
        if Selected_Station is None:
            return {}
        
        else:
            if Bacteria_Data['Station_Name'].str.contains(Selected_Station['points'][0]['text']).any():           
                station_name = Selected_Station['points'][0]['text']
                station_df = Bacteria_Data[Bacteria_Data['Station_Name'] == str(station_name)]
                station_df['Date'] = pd.to_datetime(station_df['Sample_Time'])
                station_df.set_index('Date', inplace=True)
                
    
                # Adding data for E. coli and Enterococci
                data = [dict(type="scatter",
                             mode="lines+markers",
                             name="E. coli",
                             x=station_df.index,
                             y=station_df['Ecoli'],
                             legend_orientation="h",
                             line=dict(shape="spline", smoothing=2, width=1, color="blue"),),
                
                        dict(type="scatter",
                             mode="lines+markers",
                             name="Enterococci",
                             x=station_df.index,
                             y=station_df['Enterococci'],
                             legend_orientation="h",
                             line=dict(shape="spline", smoothing=2, width=1, color="orange"),)            
                        ]
        
                layout = dict(title= {'text': Selected_Station['points'][0]['text'],
                                      'xanchor': 'center'},
                              xaxis={'title':'Sampling Date'}, 
                              yaxis={'title':'Bacteria Count [MPN/100mL]'},
                              showlegend = False,)
            else:
                station_name = Selected_Station['points'][0]['text']
                station_df = USGS_Data[USGS_Data['Station_Name'] == str(station_name)]
                station_id = station_df['Site_Number'].tolist()[0]
                StreamData = hf.NWIS(site = '0' + str(station_id), 
                                     service = 'dv', 
                                     period = 'P365D').get_data()
                StreamDataDF = StreamData.df()
                # Remove qualifier from the dataframe
                #StreamDataDF = StreamDataDF.drop(StreamDataDF.columns[1], axis=1)
                # Rename first column to flowrate
                StreamDataDF = StreamDataDF.rename(columns={StreamDataDF.columns[0]: "Flowrate"})
                
                data = [dict(type="scatter",
                             mode="lines",
                             name="Flow Rate",
                             x=StreamDataDF.index,
                             y=StreamDataDF['Flowrate'],
                             legend_orientation="h",
                             line=dict(shape="spline", smoothing=2, width=1, color="blue"),)
                    ]
                
                layout = dict(title= {'text': Selected_Station['points'][0]['text'],
                                      'xanchor': 'center'},
                              xaxis={'title':'Date [Previous 365 Days since Today]'}, 
                              yaxis={'title':'Flow Rate [cfs]'},
                              showlegend = False,)
        

        
    # Create and return figure
    figure = dict(data=data, layout = layout)
    return figure

###############################################################################
# Callback to Flow Duration Plot                                              #
###############################################################################
@app.callback(
    Output("FlowDuration", "figure"),
    [Input("station_map", "hoverData"),
     ],
)
def Make_FlowDuration_Plot(Selected_Station):  
    # Find which one has been triggered
    ctx = dash.callback_context 
    station_id = ""
    station_type = ""
    
    if ctx.triggered:
        splitted = ctx.triggered[0]["prop_id"].split(".")
        station_id = splitted[0]
        station_type = splitted[1]
    
    
    # If Point is Clicked and is on the Map:
    if station_id == "station_map" and station_type == "hoverData":
        if Selected_Station is None:
            return {}
        
        else:
            if Bacteria_Data['Station_Name'].str.contains(Selected_Station['points'][0]['text']).any():           
                return {}
            else:
                station_name = Selected_Station['points'][0]['text']
                station_df = USGS_Data[USGS_Data['Station_Name'] == str(station_name)]
                station_id = station_df['Site_Number'].tolist()[0]
                StreamData = hf.NWIS(site = '0' + str(station_id), 
                                     service = 'dv', 
                                      start_date='2018-01-01',
                                      end_date=datetime.today().strftime('%Y-%m-%d')).get_data()
                StreamDataDF = StreamData.df()
                # Remove qualifier from the dataframe
                #StreamDataDF = StreamDataDF.drop(StreamDataDF.columns[1], axis=1)
                # Rename first column to flowrate
                StreamDataDF = StreamDataDF.rename(columns={StreamDataDF.columns[0]: "Flowrate"})
                # Rank the discharge
                Qrate = StreamDataDF['Flowrate'].tolist()
                sort = np.sort(Qrate)[::-1]
                exceedence = np.arange(1.,len(sort)+1) / len(sort)
                exceedence = exceedence * 100
                
                data = [dict(type="scatter",
                             mode="lines",
                             name="Flow Rate",
                             x=exceedence,
                             y=sort,
                             legend_orientation="h",
                             line=dict(shape="spline", smoothing=2, width=1, color="blue"),)
                    ]
                
                layout = dict(title= {'text': Selected_Station['points'][0]['text'],
                                      'xanchor': 'center'},
                              xaxis={'title':'Probability of Exceedance [%] Using Data From 2010/01/01'}, 
                              yaxis={'title':'Flow Rate [cfs]',
                                     'type': 'log'},
                              showlegend = False,)
        

        
    # Create and return figure
    figure = dict(data=data, layout = layout)
    return figure
        
        
        
###############################################################################
# Make bacteria average plot
###############################################################################
@app.callback(
    Output("Bacteria_Avg", "figure"),
    [Input("station_map", "hoverData"),
     ],
)
def Make_BacteriaAvg_Plot(self):
    Bacteria_Data2 = Bacteria_Data.groupby(['Station_Name']).mean()
    
    # Adding data for E. coli and Enterococci
    data = [dict(type="scatter",
                 mode="markers",
                 name="E. coli",
                 x=Bacteria_Data2.index,
                 y=Bacteria_Data2['Ecoli'],
                 legend_orientation="h",
                 font=dict(size =8),
                 line=dict(shape="spline", smoothing=2, width=1, color="blue"),),
                
            dict(type="scatter",
                 mode="markers",
                 name="Enterococci",
                 x=Bacteria_Data2.index,
                 y=Bacteria_Data2['Enterococci'],
                 legend_orientation="h",
                 font=dict(size =8),
                 line=dict(shape="spline", smoothing=2, width=1, color="orange"),)            
            ]
        
    layout = dict(title= {'text': 'Average Bacteria Count',
                          'xanchor': 'center'},
                xaxis={'title':'Sampling Location'}, 
                yaxis={'title':'Bacteria Count [MPN/100mL]'},
                showlegend = False,)
    
    
    
    
        
    figure = dict(data=data, layout = layout)
    return figure
    
# Main
if __name__ == "__main__":
    app.run_server(debug=True)


























