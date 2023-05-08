import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

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

stations = Base.classes.station

#tobs= Base.classes.measurement

################################################
#Flask setup
################################################

# Create an instance of Flask
app = Flask(__name__)

###################################################
#Flask routes
###################################################

# Define the homepage route
@app.route("/") #decorator
def welcome():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# Define the precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    #Create session link from Python to the DB
    Session = Session(engine)

    """Return the JSON representation of dictionary containing date and precipitation data."""
    #Query precipitation data 
    results = Session.query(Measurement.date, Measurement.prcp).all()

    Session.close()
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

    #Create session link from python to DB
    Session = Session(engine)

    """Return a JSON list of stations."""
    # Perform the query to retrieve the list of stations
    results = Session.query(stations.station).all()

    Session.close()

    # Convert the query results to a list
    station_list = list(np.ravel(results))

    return jsonify(station_list)

# Define the temperature observations route
@app.route("/api/v1.0/tobs")
def tobs():
    
    #Create a session link from Python to DB
    Session = Session(engine)

    #Define most active station by station in measurement table
    most_active_st = Session.query(Measurement.station).group_by(Measurement.station)\
    .order_by(func.count().desc())\
    .first()

    #define most recent date in data set
    recent_date =  Session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    results = Session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.id == most_active_st[0])\
        .filter(func.strftime("%Y-%m-%d", Measurement.date) >= recent_date - dt.timedelta(days=365))\
        .all()

    Session.close()

#Return Jsonify list of temp observations for the previous year
    tobs_list = []
    for date, tobs in results:
            tobs_dict = {}
            tobs_dict["Date"] = date 
            tobs_dict["Temperature Obs"]= tobs
            tobs_list.append(tobs_dict)
    return jsonify(tobs_list)
   
# Define the temperature statistics route for a given start date
@app.route("/api/v1.0/<start>")
def temperature_stats_start(start):
    # Create session link from Python to the DB
    session = Session(engine)

    """Return a JSON list of the minimum temperature, average temperature, and maximum temperature
       for all the dates greater than or equal to the start date."""
    # Query temperature statistics for the given start date
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(tobs.date >= start)\
        .all()

    session.close()

    # Create a dictionary to store the temperature statistics
    temperature_stats = {
        "Start Date": start,
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temperature_stats)

# Define the temperature statistics route for a given start and end date
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats_range(start, end):
    # Create session link from Python to the DB
    session = Session(engine)

    """Return a JSON list of the minimum temperature, average temperature, and maximum temperature
       for the dates from the start date to the end date, inclusive."""
    # Query temperature statistics for the given date range
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
        .filter(Measurement.date >= start)\
        .filter(Measurement.date <= end)\
        .all()

    session.close()

    # Create a dictionary to store the temperature statistics
    temperature_stats = {
        "Start Date": start,
        "End Date": end,
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temperature_stats)

if __name__ == "__main__":
    app.run(debug=True)
