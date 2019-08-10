from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# We can view all of the classes that automap found
Base.classes.keys()
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Create the inpector previous to send queries in order to know the structure of the database
inspector = inspect(engine)
inspector.get_table_names()

# get the columns names and types of both tables

## import required libraries to manages date-time data
import datetime as dt
import pandas as pd
import numpy as np

# Design a query to retrieve the last 12 months of precipitation data and plot the results
lastDate=session.query(Measurement.date).order_by(Measurement.date.desc()).first()
lastDate=list(np.ravel(lastDate))
lastDate=dt.datetime.strptime(lastDate[0], '%Y-%m-%d').date()
# Calculate the date 1 year ago from the last data point in the database
query_date=lastDate-dt.timedelta(days=365)
# Perform a query to retrieve the data and precipitation scores
sel = [Measurement.date, 
       func.avg(Measurement.prcp)]
Precipitation=session.query(*sel).\
    filter(Measurement.date > query_date).\
    group_by(Measurement.date).\
    order_by(Measurement.date).all()
# Save the query results as a Pandas DataFrame and set the index to the date column
df = pd.DataFrame(Precipitation, columns=['date', 'prcp'])
df.set_index('date', inplace=True)
# Sort the dataframe by date
df=df.sort_index()

# Flask app
sel = [Measurement.station,
       Station.name,
       Station.latitude,
       Station.longitude,
       Station.elevation,
       func.sum(Measurement.prcp)]
Rainfall=session.query(*sel).\
    filter(Measurement.date >= '2016-12-15').\
    filter(Measurement.date <= '2016-12-31').\
    filter(Measurement.station == Station.station).\
    group_by(Measurement.station).\
    order_by(func.sum(Measurement.prcp).desc()).all()
pd.DataFrame(Rainfall, columns=["station_id", "Station Name", "latitude", "longitude", "elevation", "Rainfall"])

from flask import Flask, jsonify
app = Flask(__name__)

sel = [Measurement.station,
       Measurement.date, 
       Measurement.tobs]
sel2 = [func.avg(Measurement.tobs),
       func.max(Measurement.tobs),
       func.min(Measurement.tobs)]

qTemperature=session.query(*sel).\
    filter(Measurement.date > query_date).\
    order_by(Measurement.station, Measurement.date).all()
session.close()
df_temperature=pd.DataFrame(qTemperature, columns=["Station_id", "date", "tobs"])

@app.route("/")
def welcome():
    """All available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return precipitation data as json"""
    return jsonify(df.to_dict('dict'))
@app.route("/api/v1.0/stations")
def stations():
    """Return stations data as json"""
    dt_stations=pd.DataFrame(engine.execute('SELECT station, name, latitude, longitude, elevation FROM station').fetchall(), columns=["Station_id", "Station_Name", "latitude", "longitude", "elevation"])
    return jsonify(dt_stations.to_dict('dict'))
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature data as json"""
    return jsonify(df_temperature.to_dict('dict'))

@app.route("/api/v1.0/<start>")
def query_by_start_date(start):
    """Return temperature data as of start date"""
    qTem_start=session.query(*sel2).\
        filter(Measurement.date > start).all()
    session.close()
    df_tem_start=pd.DataFrame(qTem_start, columns=["TAVG", "TMAX", "TMIN"])
    
    return jsonify(df_tem_start.to_dict('dict'))
@app.route("/api/v1.0/<start>/<end>")
def query_by_start_end_date(start,end):
    """Return temperature data as of start date"""
    qTem_start_end=session.query(*sel2).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    session.close()
    df_tem_start_end=pd.DataFrame(qTem_start_end, columns=["TAVG", "TMAX", "TMIN"])
    
    return jsonify(df_tem_start_end.to_dict('dict'))
            
if __name__ == "__main__":
    app    .run(debug=False)