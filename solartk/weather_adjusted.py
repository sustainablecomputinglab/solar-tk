#!/usr/bin/env python
import pandas as pd 
import numpy as np
import datetime 
import math
import time
import sys
import pytz
from tzwhere import tzwhere
import csv

from irradiance import get_clearsky_irradiance
from weather import get_temperature_cloudcover
from sunpos import get_sun_position

# weather adjusted generation potential class that provides a function to compute
# weather adjusted generation
class WeatherAdjustedGeneration: 

    # a constructor to initialize the values of latitude and logitude
    def __init__(self, k=None, latitude=None, longitude=None):    

        if (latitude == None):
            raise ValueError('please specify the latitude value.')
        else:
            self.lat_ = latitude

        if (longitude == None):
            raise ValueError('please specify the longitude value.')
        else:
            self.lon_ = longitude

        # set default data sources for clearsky, sun position and temperature
        self.weather_source = 'weather_underground'

    
    def set_data_sources(self, weather_source='weather_underground'):

        # set the parameters based on the specified values
        self.weather_source = weather_source

    # a function to compute maximum generation potential for the given system at time t
    # clearsky method and method for computing sun position are optional arguments
    def adjusted_weather_generation(self, max_generation=None):

        # extract the start and end times from the data
        start_time = max_generation.iloc[0][0]
        end_time = max_generation.iloc[-1][0]

        # get the resolution of the data as number of seconds between two consecutive timestamps
        granularity = (max_generation.iloc[1][0] - max_generation.iloc[0][0]).seconds

        # get weather data
        temp_cloudcover = get_temperature_cloudcover(start_time=start_time, 
                            end_time=end_time, granularity=granularity, latitude=self.lat_, 
                            longitude=self.lon_, source=self.weather_source)

        # print(temp_cloudcover)

        # combined with max_generation data
        adjusted_generation = max_generation.join(temp_cloudcover.set_index('time'), on='time')

        # apply weather effect
        adjusted_generation['weather_effect'] = (0.985 - 0.984 * ((adjusted_generation['clouds']/100) ** 3.4))
        adjusted_generation['adjusted_generation'] = adjusted_generation['weather_effect']*pd.to_numeric(adjusted_generation['max_generation'])

        # just keep the time and adjusted_generation columns
        adjusted_generation = adjusted_generation[['time', 'adjusted_generation']]
        adjusted_generation.columns = ['#time', 'adjusted_generation']

        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            adjusted_generation.to_csv(sys.stdout, index=False, header='False')


if __name__ == "__main__":

    # read data from stdin, split by line, and split each line by comma
    data = pd.DataFrame([line for line in csv.reader(sys.stdin)])

    # get latitude and longitude
    lat, lon = data.iloc[1][0], data.iloc[1][1]

    # remove the first two rows
    data = data[2:].reset_index(drop=True)

    # set first row as column which contain #time, max_generation
    data.columns = data.iloc[0]
    data = data.reindex(data.index.drop(0)).reset_index(drop=True)
    data.columns.name = None
    data = data.replace(to_replace='None', value=np.nan).dropna()

    # convert time column to datetime
    data['time'] = pd.to_datetime(data['#time'])
    data = data[['time', 'max_generation']]

    ##################### for future release #######################
    # # read user input from command line
    # user_args = sys.argv
    # start_time, end_time, resolution = user_args[1], user_args[2], float(user_args[3])
    ################################################################

    # create an object of GenerationPotential class    
    weather = WeatherAdjustedGeneration(latitude=lat, longitude=lon)

    # compute weather adjusted generation
    weather.adjusted_weather_generation(max_generation=data)