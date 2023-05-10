import datetime as dt
from datetime import date
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import sqlite3
from flask import Flask, jsonify

########################################################
#Database Setup
########################################################

engine = create_engine("sqlite:///hawaii.sqlite")

#reflect an exsisting database into new model
Base = automap_base()

#reflect the tables
Base.prepare(autoload_with=engine)

Measurement = Base.classes.measurement
station = Base.classes.station

################################################
#Flask setup
################################################
session = Session(engine)
# Create an instance of Flask
app = Flask(__name__)

###################################################
#Flask routes
###################################################

# Define the homepage route
@app.route("/")
def homepage():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start(yyyy-mm-dd)<br/>"
        f"/api/v1.0/start(yyyy-mm-dd)/end(yyyy-mm-dd)<br/>"
    )

# Define the precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the JSON representation of dictionary containing date and precipitation data."""
    #Query precipitation data 
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()

    # Perform the query to retrieve the date and precipitation data
    query_results = []
    for date, prcp in results:
        precipitation_dict = {}
        precipitation_dict["Date"] = date
        precipitation_dict["Precipitation"] = prcp
        query_results.append(precipitation_dict)

    return jsonify(query_results)

# Define the stations route
@app.route("/api/v1.0/stations")
def stations():  

    """Return a JSON list of stations."""
    # Perform the query to retrieve the list of stations
    results = session.query(station.station, station.name).all()

    session.close()

    # Convert the query results to a list
    station_list = list(np.ravel(results))

    return jsonify(station_list)

# Define the temperature observations route
@app.route("/api/v1.0/tobs")
def tobs(): 

    # Calculate the date one year ago from the last date in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], "%Y-%m-%d").date()
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()

    # Query the temperature observations for the previous year
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station[0]).\
        filter(Measurement.date >= one_year_ago).all()

    # Close the session
    session.close()

    # Create a dictionary with the temperature observations
    temperature_observations = []
    for date, tobs in results:
        temperature_observations.append({"date": date, "tobs": tobs})

    # Return the JSON list of temperature observations
    return jsonify(temperature_observations)

@app.route("/api/v1.0/<start_date>")
def temp_start(start_date):
    # Calculate minimum, average and maximum temperatures for the range of dates starting with start date.
    # If no end date is provided, the function defaults to 2017-08-23.
    start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    #session = Session(engine)
    query_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).all()
    session.close()

    temp_stats = []
    for min, avg, max in query_result:
        temp_dict = {}
        temp_dict["Min"] = min
        temp_dict["Average"] = avg
        temp_dict["Max"] = max
        temp_stats.append(temp_dict)

    return jsonify(temp_stats)
    
  
@app.route("/api/v1.0/<start_date>/<end_date>")
def temp_st_end(start_date,end_date):
    # Calculate minimum, average and maximum temperatures for the range of dates starting with start date.
    start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    #session = Session(engine)
    query_result = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    
    session.close()

    temp_stats = []
    for min, max, avg in query_result:
        temp_dict = {}
        temp_dict["Min"] = min
        temp_dict["Max"] = max
        temp_dict["Average"] = avg
        temp_stats.append(temp_dict)

    # If the query returned non-null values return the results,otherwise return an error message
    if temp_dict['Min']: 
        return jsonify(temp_stats)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404

if __name__ == "__main__":
    app.run(debug=True)

