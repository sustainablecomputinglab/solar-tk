import datetime
import pysolar
import pytz
import pandas as pd
import requests
import os 
import googlemaps
import numpy as np

from helpers import granularity_to_freq

from typing import List, Dict, Tuple

def get_clearsky_irradiance(start_time: datetime.datetime = None, end_time: datetime.datetime = None, timezone: pytz.timezone = None, 
                latitude: float = None, longitude: float = None, sun_zenith: pd.DataFrame = None, 
                granularity: int = 60, clearsky_estimation_method: str = 'pysolar', 
                google_api_key: str = None):



    if (clearsky_estimation_method == 'pysolar' or google_api_key==None):

        ################################################################################## 
        # 
        # Pandas .apply based code, but it is slower than while loop
        # from helpers import granularity_to_freq
        #       
        # datetime_series = pd.date_range(start_time, end_time, freq=granularity_to_freq(granularity))
        # datetime_series_localized = datetime_series.tz_localize(timezone)
        # data = pd.DataFrame({'time':datetime_series_localized})
        # data['altitude_deg'] = data['time'].apply(lambda timestamp: pysolar.solar.get_altitude(latitude, longitude, timestamp))
        # data['clearsky'] = data.apply(lambda row: pysolar.solar.radiation.get_radiation_direct(row['time'], row['altitude_deg']), axis=1)
        # data['time'] = data['time'].apply(lambda x: x.replace(tzinfo=pytz.utc).replace(tzinfo=None))  
        ################################################################################## 

        # localizing the datetime based on the timezone
        start: datetime.datetime = timezone.localize(start_time)
        end: datetime.datetime = timezone.localize(end_time)

        # create arrays to store time and irradiance
        clearsky: List[int] = []
        time_: List[datetime.datetime] = []

        # go through all the hours between the two dates
        while start <= end:

            # get the altitude degree for the given location
            altitude_deg: float = pysolar.solar.get_altitude(latitude, longitude, start)

            # get the clearsky based on the time and altitude
            clear_sky: float = pysolar.solar.radiation.get_radiation_direct(start, altitude_deg)

            # removing the timezone information
            dt: datetime.datetime = start.replace(tzinfo=pytz.utc).replace(tzinfo=None)

            # saving the data in the lists
            clearsky.append(clear_sky)
            time_.append(dt)
            
            # increasing the time by 1 hrs, normazlizing it to handle DST
            start = timezone.normalize(start + datetime.timedelta(seconds = granularity))

        # create dataframe from lists
        irradiance: pd.DataFrame = pd.DataFrame({'time':time_,'clearsky':clearsky})

    elif (clearsky_estimation_method == 'lau_model' and google_api_key!=None):

        # use google maps python api to get elevation
        gmaps = googlemaps.Client(key=google_api_key)
        elevation_api_response:list = gmaps.elevation((latitude, longitude))
        elevation_km:float = elevation_api_response[0]['elevation']/1000

        # create a date_range and set it as a time column in a dataframe
        datetime_series = pd.date_range(start_time, end_time, freq=granularity_to_freq(granularity))
        # datetime_series_localized = datetime_series.tz_localize(timezone)
        irradiance = pd.DataFrame({'time':datetime_series})

        # based on "E. G. Laue. 1970. The Measurement of Solar Spectral Irradiance at DifferentTerrestrial Elevations.Solar Energy13 (1970)", 
        # Check details on this model on Section 2.4 on PVeducation.org
        irradiance['air_mass'] = 1/(np.cos(sun_zenith) + 0.50572*pow(96.07995 - np.rad2deg(sun_zenith), -1.6364))
        irradiance['clearsky_direct'] = 1.361*((1 - 0.14*elevation_km)*pow(0.7,irradiance['air_mass']**0.678) + 0.14*elevation_km)
        irradiance['clearsky'] = 1000*1.1*irradiance['clearsky_direct']

        # replace nan with 0 and keep only time and clearsky columns
        irradiance['clearsky'] = irradiance['clearsky'].fillna(0)
        irradiance = irradiance[['time', 'clearsky']]

    else: 
        raise ValueError('Invalid argument for clearsky_estimation_method or google_api_key.')

    return irradiance

    
    