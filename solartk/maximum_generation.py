#!/usr/bin/env python
import pandas as pd 
import numpy as np
import datetime 
import math
import time
import sys
import pytz
from tzwhere import tzwhere

from irradiance import get_clearsky_irradiance
from weather import get_temperature_cloudcover
from sunpos import get_sun_position
from helpers import granularity_to_freq


# maximum generation potential class that provides a function to find the maximum generation 
# potential of a solar site at any time t
class GenerationPotential: 

    # a constructor to initialize the values of k, tilt, orientation, temperature coefficient, latitude and logitude
    def __init__(self, k=None, tilt=None, orientation=None, latitude=None, longitude=None, baseline_temperature=25, temperature_coefficient=0.5):
        
        if (k == None or k <= 0):
            raise ValueError('please specify the k value, where k > 0.')
        else:
            self.k = k * 0.20 # convert back to k at 20% efficiency

        if (tilt == None or tilt < 0):
            raise ValueError('please specify the tilt value, where tilt => 0.')
        else:
            self.tilt_ = math.radians(tilt) 

        if (orientation == None or orientation < 0):
            raise ValueError('please specify the orientation value, where orientation => 0.')
        else:
            self.ore_ = math.radians(orientation)      

        if (latitude == None):
            raise ValueError('please specify the latitude value.')
        else:
            self.lat_ = latitude

        if (longitude == None):
            raise ValueError('please specify the longitude value.')
        else:
            self.lon_ = longitude

        self.t_baseline = baseline_temperature
        self.c = temperature_coefficient 

        # set default data sources for clearsky, sun position and temperature
        self.clearsky_source = 'pysolar'
        self.sun_position_source = 'psa'
        self.temperature_source = 'weather_underground'

    
    def set_data_sources(self, clearsky_source='pysolar', sun_position_source='psa', temperature_source='darksky'):

        # set the parameters based on the specified values
        self.clearsky_source = clearsky_source
        self.sun_position_source = sun_position_source
        self.temperature_source = temperature_source

    # a function to compute maximum generation potential for the given system at time t
    # clearsky method and method for computing sun position are optional arguments
    def maximum_generation(self, start_time=None, end_time=None, granularity=60):

        # if time is not defined or defined as something other than datetime object, raise an error
        if (start_time == None or end_time == None or isinstance(start_time, datetime.datetime) == False or isinstance(end_time, datetime.datetime) == False):
            raise ValueError('please specify the correct start and end times as a datetime object.')

        #calculate the timezone of the given latitude and longitude
        tz = tzwhere.tzwhere()
        timezone_str = tz.tzNameAt(self.lat_, self.lon_)
        timezone = pytz.timezone(timezone_str)

        # get clearsky using the defined clearsky method
        clearsky_irradiance = get_clearsky_irradiance(
                                start_time=start_time, end_time=end_time, timezone=timezone, 
                                granularity=granularity, latitude=self.lat_, longitude=self.lon_, 
                                clearsky_source=self.clearsky_source)
        
        # get sun position
        sun_position = get_sun_position(
                            start_time= start_time.replace(tzinfo=timezone).astimezone(pytz.timezone('UTC')), 
                            end_time=end_time.replace(tzinfo=timezone).astimezone(pytz.timezone('UTC')), 
                            granularity=granularity, latitude=self.lat_, longitude=self.lon_)

        # # get ambient air temperature
        t_ambient = get_temperature_cloudcover(start_time=start_time, 
                        end_time=end_time, granularity=granularity, latitude=self.lat_, 
                        longitude=self.lon_, source='weather_underground', timezone=timezone)

        # get ambient temperature 
        t_ambient = clearsky_irradiance.join(t_ambient.set_index('time'), on='time')

        # compute maximum power generation, reusing clearsky dataframe to get time as well
        clearsky_irradiance['max_power'] = clearsky_irradiance['clearsky'] * self.k * (
            1 + self.c*(self.t_baseline - t_ambient['temperature']))*(
            np.cos(math.radians(90)-pd.to_numeric(sun_position['sun_zenith']))
            *np.sin(self.tilt_)
            *np.cos(pd.to_numeric(sun_position['sun_azimuth'])-self.ore_) 
            +np.sin(math.radians(90)-pd.to_numeric(sun_position['sun_zenith']))
            *np.cos(self.tilt_))

        # just keep the time and max_power columns
        max_generation = clearsky_irradiance[['time', 'max_power']]
        max_generation.columns = ['#time', 'max_generation']

        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            max_generation.to_csv(sys.stdout, index=False, header='False')


if __name__ == "__main__":

    # read user input from command line
    user_args = sys.argv
    start_time, end_time, resolution = user_args[1], user_args[2], float(user_args[3])

    # if user input only 4 arguments, expect arguments from the pipeline
    if (len(user_args) < 5):
        data = sys.stdin.read().split()
        data = [float(i) for i in data]
        lat, lon, k_, tilt_, ore_, c_, tBase_ = data[0], data[1], data[2], data[3], data[4], data[5], data[6]
        sys.stdin.close()
    else: 
        user_args = sys.argv
        start_time, end_time, resolution, lat, lon, k_, tilt_, ore_, c_, tBase_ = user_args[1], user_args[2], user_args[3], user_args[4], user_args[5], user_args[6], user_args[7], user_args[8], user_args[9], user_args[10]

    # create an object of GenerationPotential class
    gen = GenerationPotential(k=k_, tilt=tilt_, orientation=ore_, temperature_coefficient=c_, latitude=lat, longitude=lon, baseline_temperature=tBase_)

    start_time_ = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time_ = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    print("#latitude(°),longitude(°)")
    print("{},{}".format(lat, lon))
    
    gen.maximum_generation(start_time=start_time_, end_time=end_time_, granularity=resolution)