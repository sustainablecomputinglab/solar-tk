#!/usr/bin/env python
import sys
import pandas as pd
import pytz
from tzwhere import tzwhere
import numpy as np
import math
from sklearn import metrics

from irradiance import get_clearsky_irradiance
from weather import get_temperature_cloudcover
from sunpos import get_sun_position


#debug code 
import matplotlib.pyplot as plt 



class ParameterModeling:
    
    # a constructor to initialize the values of latitude, logitude, and the file name
    def __init__(self, latitude=None, longitude=None, data_file=None):  

        # set default data sources for clearsky, sun position and temperature
        self.clearsky_estimation_method = 'lau_model'
        self.sun_position_source = 'psa'
        self.temperature_source = 'darksky'
        self.google_api_key = ' '
        self.darksky_api_key = ' '

        if (latitude == None):
            raise ValueError('please specify the latitude value.')
        else:
            self.lat_ = float(latitude)

        if (longitude == None):
            raise ValueError('please specify the longitude value.')
        else:
            self.lon_ = float(longitude)

        try: 
            self.data = pd.read_csv(data_file)
            self.data['time'] = pd.to_datetime(self.data['time'])
            self.data = self.data.sort_values(by=['time'], ascending=True).reset_index(drop=True)

            # extract the start and end times from the data
            self.start_time = self.data.iloc[0][0]
            self.end_time = self.data.iloc[-1][0]

            # get the resolution of the data as number of seconds between two consecutive timestamps
            self.granularity = (self.data.iloc[1][0] - self.data.iloc[0][0]).seconds

            #calculate the timezone of the given latitude and longitude
            tz = tzwhere.tzwhere()
            timezone_str = tz.tzNameAt(self.lat_, self.lon_)
            self.timezone = pytz.timezone(timezone_str)

        except:
            print('The file could not be opened.')
            raise

    def upperlimit_violation_count(self, x):
        return len(x[x['max'] < x['solar']])
    
    def root_mean_squared_error(self, prediction, accurate):
        return np.sqrt(metrics.mean_squared_error(accurate, prediction))

    def get_onetime_data(self):

        # get sun position
        sun_position = get_sun_position(
                            start_time=self.start_time.replace(tzinfo=self.timezone).astimezone(pytz.timezone('UTC')), 
                            end_time=self.end_time.replace(tzinfo=self.timezone).astimezone(pytz.timezone('UTC')), 
                            granularity=self.granularity, latitude=self.lat_, longitude=self.lon_)

        self.data['sun_azimuth'] = sun_position['sun_azimuth']
        self.data['sun_zenith'] = sun_position['sun_zenith']

        # get clearsky using the defined clearsky method
        clearsky_irradiance = get_clearsky_irradiance(
                                start_time=self.start_time, end_time=self.end_time, timezone=self.timezone, 
                                granularity=self.granularity, latitude=self.lat_, longitude=self.lon_, 
                                clearsky_estimation_method=self.clearsky_estimation_method, sun_zenith=self.data['sun_zenith'], google_api_key=self.google_api_key)

        self.data['clearsky'] = clearsky_irradiance['clearsky']
        
        # get ambient air temperature
        t_ambient = get_temperature_cloudcover(start_time=self.start_time, 
                        end_time=self.end_time, granularity=self.granularity, latitude=self.lat_, 
                        longitude=self.lon_, source=self.temperature_source, timezone=self.timezone, darksky_api_key=self.darksky_api_key)

        # get ambient temperature 
        filtered = self.data.join(t_ambient.set_index('time'), on='time')
        self.data['temperature'] = filtered['temperature']

    def preprocess_data(self):

        # print(self.data)
        
        # remove all the times when solar power is zero
        self.data = self.data[self.data.solar > 0]

        # get the date from the 
        self.data['date'] = self.data['time'].dt.date

        # print(self.data)
        
        # delete the first and last hours of the day
        self.data = self.data.groupby('date', as_index=False).apply(lambda group: group.iloc[2:]).reset_index()
        self.data = self.data.drop(['level_0', 'level_1'], axis = 1)
        self.data = self.data.groupby('date', as_index=False).apply(lambda group: group.iloc[:-2]).reset_index()
        self.data = self.data.drop(['level_0', 'level_1'], axis = 1)
        
        # convert kw to watts
        self.data['solar'] = 1000*self.data['solar']

        ### debug comment: keeping date column for later use ###
        # drop the date_only column
        # self.data = self.data.drop('date_only', 1)

    def find_parameters(self):

        # print(self.data)

        best_k = 100
        best_tilt = math.radians(self.lat_)
        best_ori = math.radians(180)
            
        for run in range(10):

            # best_k = float(input('Please input k: '))
            # best_tilt = np.deg2rad(int(input('Please input tilt: ')))
            # best_ori = np.deg2rad(int(input('Please input orientation: ')))
        
            # search for best k
            best_k = self.find_K(best_tilt, best_ori, run)

            self.data['max'] = self.data['clearsky'] * best_k * (
            1 + 0.005*(16 - self.data['temperature'])) *(
                np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.sin(best_tilt)
                *np.cos(pd.to_numeric(self.data['sun_azimuth'])-best_ori) 
                +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.cos(best_tilt))

            print(self.data)

            if run == 0:
                add_k = 2
            else:
                add_k = 0

            # # search for best orientation
            best_ori = self.find_ori(best_k + add_k, best_tilt, run)
            # best_ori = np.deg2rad(180)   
            # self.find_ori(best_k + add_k, best_tilt, run)
            
            # # search for best tilt
            best_tilt = self.find_tilt(best_k + add_k, best_ori, self.lat_, run)
            # best_tilt = np.deg2rad(50)

            print(best_k, np.rad2deg(best_ori), np.rad2deg(best_tilt))
            # debug code
            # self.data['max'] = self.data['clearsky'] * best_k * (
            # 1 + 0.005*(25 - self.data['temperature'])) *(
            #     np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
            #     *np.sin(best_tilt)
            #     *np.cos(pd.to_numeric(self.data['sun_azimuth'])-best_ori) 
            #     +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
            #     *np.cos(best_tilt))
            
            # # debug code
            # plt.plot([i for i in range(len(self.data))], self.data['max'], label='Max Solar ({})'.format(best_k))
            # plt.plot([i for i in range(len(self.data))], self.data['solar'], label='Solar')
            # plt.legend()
            # plt.title('Graph with K')
            # plt.show()  

        return best_k, math.degrees(best_tilt), math.degrees(best_ori)
 
    def find_K(self, tilt_, ori_, iter_):

        # initialize some variables
        k_ = 0
        k_tolerance = 2
        
        rmse_list = []
        k_list = []

        #debug code
        # print(tilt_, ori_)

        for k_ in range(0, 1000, 1):
            
            k_ = k_/10

            # compute maximum power generation for the given parameters
            self.data['max'] = self.data['clearsky'] * k_ * (
                np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.sin(tilt_)
                *np.cos(pd.to_numeric(self.data['sun_azimuth'])-ori_) 
                +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.cos(tilt_))

            # count how many times upperlimit has been violated for each day
            count = self.data.groupby(['date']).apply(self.upperlimit_violation_count)

            # print(count)
            # break

            ##########################################################################
            # debug code
            # if ((k_ % 3 == 0) and (6<= k_ <= 12) and (iter_ == 1)):
            #     plt.plot([i for i in range(len(self.data))], self.data['max'], label='Max Solar ({})'.format(k_))
            #     plt.plot([i for i in range(len(self.data))], self.data['solar'], label='Solar')
            #     plt.legend()
            #     plt.title('Graph with K')
            #     plt.show()  
            ##########################################################################

            # # check if count > tolerance
            # if iter_ <0: 
            #     k_list.append(k_)
            #     rmse_ = np.sqrt(metrics.mean_squared_error(self.data['solar'], self.data['max']))
            #     rmse_list.append(rmse_) 
            #     k_flag = True               
            # else:
            # if count <= k_tolerance:


            # (count > k_tolerance).any()

            if (count > k_tolerance).any():
                k_list.append(k_) 
                rmse_list.append(np.inf)
                # print(k_, np.inf, any(count))
            else: 
                k_list.append(k_)
                rmse_list.append(self.root_mean_squared_error(self.data['max'], self.data['solar']))
                # print(k_, self.root_mean_squared_error(self.data['max'], self.data['solar']))

            # if k_ > 10:
            #     break

        ##### debug code
        # k_flag = True
        # print(len(rmse_list))
        # print(self.data['max'])
        
        # if we could find the parameters
        if any(rmse_list) != np.inf:      
            minimum_rmse = min(rmse_list)
            index_min_rmse = rmse_list.index(minimum_rmse)
        else:
            return 100


        ##########################################################################
        # print(k_list[index_min_rmse])

        # debug code
        self.data['max'] = self.data['clearsky'] * k_list[index_min_rmse] * (
            np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
            *np.sin(tilt_)
            *np.cos(pd.to_numeric(self.data['sun_azimuth'])-ori_) 
            +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
            *np.cos(tilt_))
        
        # debug code
        plt.plot([i for i in range(len(self.data))], self.data['max'], label='Max Solar ({})'.format(k_list[index_min_rmse]))
        plt.plot([i for i in range(len(self.data))], self.data['solar'], label='Solar')
        plt.legend()
        plt.title('Graph with K')
        plt.show()  
        ##########################################################################

        return k_list[index_min_rmse]

    def find_ori(self, k_, tilt_, iter_):

        # initialize
        ori_flag = False
        rmse_list = []
        ori_list = []
        ori_tolerance = 1
        
        for ori_ in np.arange(0, math.radians(360), math.radians(1)):

            # compute maximum power generation for the given parameters
            self.data['max'] = self.data['clearsky'] * k_ * (
                np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.sin(tilt_)
                *np.cos(pd.to_numeric(self.data['sun_azimuth'])-ori_) 
                +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.cos(tilt_))

            # count the times when max is less than solar
            count = len(self.data[self.data['max'] < self.data['solar']])

            ##########################################################################
            # debug code
            # if ((ori_ % math.radians(40) == 0)):
            #     plt.plot([i for i in range(len(self.data))], self.data['max'], label='Max Solar')
            #     plt.plot([i for i in range(len(self.data))], self.data['solar'], label='Solar')
            #     plt.legend()
            #     plt.show()  
            ##########################################################################

            # check if count > tolerance
            if iter_ < 1: 
                ori_list.append(ori_)
                rmse_ = np.sqrt(metrics.mean_squared_error(self.data['solar'], self.data['max']))
                rmse_list.append(rmse_)
                ori_flag = True
            else: 
                if count <= ori_tolerance:
                    ori_list.append(ori_)
                    rmse_ = np.sqrt(metrics.mean_squared_error(self.data['solar'], self.data['max']))
                    rmse_list.append(rmse_)
                    ori_flag = True
                    ### debug code 
                    # print("Ori: ", ori_, ", RMSE: ", rmse_) 
                else: 
                    ori_list.append(ori_)
                    rmse_list.append(np.inf)
                    ### debug code 
                    # print("Ori: ", ori_, ", RMSE: ", np.inf) 
            
        # if we could find the parameters
        if(ori_flag == True):      
            minimum_rmse = min(rmse_list)
            index_min_rmse = rmse_list.index(minimum_rmse)
        else:
            return math.radians(180)

        ##########################################################################
        # print(k_list[index_min_rmse])

        # # debug code
        # self.data['max'] = self.data['clearsky'] * k_ *(
        #     np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
        #     *np.sin(tilt_)
        #     *np.cos(pd.to_numeric(self.data['sun_azimuth'])-ori_list[index_min_rmse]) 
        #     +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
        #     *np.cos(tilt_))
        
        # ## debug code
        # plt.plot([i for i in range(len(self.data))], self.data['max'], label='Max Solar (Ori)')
        # plt.plot([i for i in range(len(self.data))], self.data['solar'], label='Solar')
        # plt.show()  
        ##########################################################################
            
        return ori_list[index_min_rmse]

    def find_tilt(self, k_, ori_, latitude, iter_):

        # initialize
        tilt_flag = False
        rmse_list = []
        tilt_list = []
        tilt_tolerance = 1
        
        for tilt_ in np.arange(math.radians(latitude - 20), math.radians(latitude + 20), math.radians(0.1)):

            # compute maximum power generation for the given parameters
            self.data['max'] = self.data['clearsky'] * k_ *(
                np.cos(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.sin(tilt_)
                *np.cos(pd.to_numeric(self.data['sun_azimuth'])-ori_) 
                +np.sin(math.radians(90)-pd.to_numeric(self.data['sun_zenith']))
                *np.cos(tilt_))

            # count the times when max is less than solar
            count = len(self.data[self.data['max'] < self.data['solar']])

            # check if count > tolerance
            if iter_ < 1:
                tilt_list.append(tilt_)
                rmse_ = np.sqrt(metrics.mean_squared_error(self.data['solar'], self.data['max']))
                rmse_list.append(rmse_)
                tilt_flag = True
            else:
                if count <= tilt_tolerance:
                    tilt_list.append(tilt_)
                    rmse_ = np.sqrt(metrics.mean_squared_error(self.data['solar'], self.data['max']))
                    rmse_list.append(rmse_)
                    tilt_flag = True
                else: 
                    tilt_list.append(tilt_)
                    rmse_list.append(np.inf)
            
        # if we could find the parameters
        if(tilt_flag == True):      
            minimum_rmse = min(rmse_list)
            index_min_rmse = rmse_list.index(minimum_rmse)
        else:
            return math.radians(latitude)
        
        return tilt_list[index_min_rmse]

    def find_temp_coefficients(self, k_, tilt_, ori_):
        
        # to be implemented in the future release
        # return standard values for now
        return 0, 0.005

if __name__ == "__main__":

    # read user input from command line
    user_args = sys.argv

    # if user input only 4 arguments, expect arguments from the pipeline
    if (len(user_args) >= 4):
        lat, lon, file_ = user_args[1], user_args[2], user_args[3]
    else: 
        print("Please input latitude, longitude, and historical generation data file.")

    # initialize the file name, latitude, and longitude
    parameters = ParameterModeling(latitude=lat, longitude=lon, data_file=file_)

    # gather sun position, clearsky, and temperature data at the start
    parameters.get_onetime_data()

    # preprocess data to remove night times and first/last hours
    parameters.preprocess_data()

    # parameters.data['sun_azimuth'] = parameters.data['sun_azimuth'].shift(1)
    # parameters.data['sun_zenith'] = parameters.data['sun_zenith'].shift(1)
    # parameters.data['clearsky'] = parameters.data['clearsky'].shift(1)

    # parameters.data = parameters.data.fillna(0)
    # print(parameters.data)

    # find paramaters
    k_, tilt_, ori_ = parameters.find_parameters()

    # print(parameters.data)

    t_base, c_ = parameters.find_temp_coefficients(k_, tilt_, ori_)

    print(lat, lon, k_/0.18, tilt_, ori_, c_, t_base)