from flask import Flask, jsonify

import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def welcome():
    """List all available api routes."""
    return ('''
    Available Routes:<br><br>
    /api/v1.0/precipitation<br>
    /api/v1.0/stations<br>
    /api/v1.0/tobs<br>
    /api/v1.0/"start_date"*<br>
    /api/v1.0/"start_date"/"end_date"*<br><br>
    *dates format should be yyyy-mm-dd
    ''')

@app.route("/api/v1.0/precipitation")
def precipitation():

    """Lists the last 12 months of precipitation data in inches per day"""

    # Open sessions
    session = Session(bind=engine)

    # Find out what is the latest date with data
    lastDate=session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    for date in lastDate:
        dataArray = date.split("-")
        (year,month,day) = dataArray
    
    # Calculate the sate 1 year ago of the latest date
    year_ago = dt.date(int(year),int(month),int(day)) - dt.timedelta(days=365)

    # Define the varialbles for start and end date
    latestPrcpDate=f'{year}-{month}-{day}'
    oldestPrcpDate=year_ago.isoformat()

    # Initiating an empty dictionary
    precipitation={}

    # Query DB for preciitation values from start date to end date
    results=session.query(Measurement).filter(Measurement.date >= year_ago).all()
    for row in results:
        prcp={row.date:row.prcp} #storing the date and the measured value in a dictionary
        precipitation.update(prcp) #updating the main dictionary with the previous smaller dictionary

    # Calculating the main API dictionary with an info key, a date interval and the results/observations 
    precipitationAPI={'info':'Last 12 months of precipitation data in inches',
                 'date interval':{'from':oldestPrcpDate,'to':latestPrcpDate},
                 'results':precipitation
                 }

    # Returing the main dictionary in a JSON format API response 
    return jsonify(precipitationAPI)
    

@app.route("/api/v1.0/stations")
def stations():

    """Lists the available stations responsible for the observations"""

    # Open sessions
    session = Session(bind=engine)

    # Query DB for StationID and Station Name
    results=session.query(Station.station,Station.name).all()

    # Initiating an empty dictionary
    stations={}

    # Going over the results and storing them in stations dict reated previously
    for id,name in results:
        station={id:name}
        stations.update(station)

    # Main API dict that holds an info key and a stations key with the stations ids and names
    stationsAPI={'info':'Available stations responsible for the observations',
        'stations':stations
    }
    
    # Returing the main dictionary in a JSON format API response 
    return jsonify(stationsAPI)


@app.route("/api/v1.0/tobs")
def tobs():

    """Lists the last 12 months of temperature observation in Fahrenheit for the Station with more observations"""

    # Open sessions
    session = Session(bind=engine)

    # Query DB for StationID, Station Name of the most active station (i.e. the station with more tempt observations) 
    data=session.query(Measurement.station,Station.name,func.count(Measurement.tobs)).\
        filter(Measurement.station==Station.station).\
        group_by(Measurement.station,Station.station).\
        order_by(func.count(Measurement.tobs).desc()).\
        first()
    
    # Unpaking the results
    (maxStationID,maxStationName,temp) = data

    # Now that we have the most active station, we need to figure out what is the last observation date.
    lastDate=session.query(Measurement.date).filter(Measurement.station == maxStationID).order_by(Measurement.date.desc()).first()
    for date in lastDate:
        dataArray = date.split("-")
        (year,month,day) = dataArray

    # And calculate what is 1 year before that to have the start and end date for the data
    year_agoStation = dt.date(int(year),int(month),int(day)) - dt.timedelta(days=365)
    
    # Store as variables
    latestTobsDate=f'{year}-{month}-{day}'
    oldestTobsDate=year_agoStation.isoformat()

    # Initiating an empty dictionary
    tobs={}

    # Query the DB once again to get the date and the respective obs value
    results=session.query(Measurement).filter(Measurement.date >= year_agoStation).filter(Measurement.station == maxStationID).all()
    for row in results:
        temp={row.date:row.tobs} #temporary dictionary with the date as key and the obs as the value
        tobs.update(temp) #append to the tobs dictionary
    
    # Also creating a dictionary to provide the user with information of the most active station
    maxStation={'id':maxStationID,
            'name':maxStationName}
    
    # Main API dict that holds an info key, the most active station, the date interval and the results/obs per day
    temperaturesAPI={'info':'Last 12 months of temperature observation in Fahrenheit for the Station with more observations',
        'most active station':maxStation,
        'date interval':{'from':oldestTobsDate,'to':latestTobsDate},
        'results':tobs
        }
    
    # Returing the main dictionary in a JSON format API response 
    return(jsonify(temperaturesAPI))


@app.route("/api/v1.0/<start>")
def tempStatsStart(start):

    """Lists the maximum, average and minimum temperature in F in Hawaii from given start date"""

    # Open sessions
    session = Session(bind=engine)

    # Split the date entered by the user in YYYY-MM-DD format
    dataArray = start.split("-")
    (year,month,day) = dataArray
    startDate=f'{year}-{month}-{day}'

    # Query DB to get the max, avg and min temperature from the date selected until the last date of observations 
    results=session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= startDate).all()
    
    # Unpacking the results
    for value in results:
        (tempMin,tempAvg,tempMax)=value

    # Creating a dictionary that holds the values queried
    startTobs={
        'minimum temperature':round(tempMin,2),
        'average temperature':round(tempAvg,2),
        'maximum temperature':round(tempMax,2)
        }
    
    # Main API dictionary that just has an additional info key for the user to know what is being queried
    startAPI={
        'info': f'Maximum, average and minimum temperature in F in Hawaii from {start} on',
        'results':startTobs
    }

    # Returing the main dictionary in a JSON format API response 
    return(jsonify(startAPI))
    
    
@app.route("/api/v1.0/<start>/<end>")
def tempStatsStartEnd(start,end):

    """Lists the maximum, average and minimum temperature in F in Hawaii from given start and end date"""

    # Open sessions
    session = Session(bind=engine)

    # Split the start and end date entered by the user in YYYY-MM-DD format
    dataStartArray = start.split("-")
    dataEndArray = end.split("-")
    (startyear,startmonth,startday) = dataStartArray
    (endyear,endmonth,endday) = dataEndArray
    startDate=f'{startyear}-{startmonth}-{startday}'
    endDate=f'{endyear}-{endmonth}-{endday}'

    # Query DB to get the max, avg and min temperature in between the dates selected
    results=session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= startDate).filter(Measurement.date <= endDate).all()

    # Unpacking the results
    for value in results:
        (tempMin,tempAvg,tempMax)=value

    # Creating a dictionary that holds the values queried
    startEndTobs={
        'minimum temperature':round(tempMin,2),
        'average temperature':round(tempAvg,2),
        'maximum temperature':round(tempMax,2)
        }
    
    # Main API dictionary that just has an additional info key for the user to know what is being queried
    startEndAPI={
        'info': f'Maximum, average and minimum temperature in F in Hawaii from {start} to {end}',
        'results':startEndTobs
    }

    # Returing the main dictionary in a JSON format API response 
    return(jsonify(startEndAPI))

# Make this ocde run from this file
if __name__ == "__main__":
    app.run(debug=True)
    