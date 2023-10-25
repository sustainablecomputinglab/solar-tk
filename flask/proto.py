from flask import Flask, request, render_template, jsonify
import requests
import pandas as pd
import urllib.parse
import time
import math
import os
import numpy as np
from zipfile import ZipFile
from sunpos import sunpos


app = Flask(__name__)

TEMP_DIR = os.path.join(os.path.expanduser("~"), "temp")
SOLAR_DATA_DIR = os.path.join(TEMP_DIR, "solar_data")

if not os.path.exists(TEMP_DIR):
    os.mkdir(TEMP_DIR)
if not os.path.exists(SOLAR_DATA_DIR):
    os.mkdir(SOLAR_DATA_DIR)

BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.json?"

class SolarTKMaxPowerCalculator:
    def __init__(self, tilt, orientation, k, c=0.05, t_baseline=25):
        self.tilt_ = math.radians(tilt)
        self.orientation = math.radians(orientation)
        self.k = k
        self.c = c
        self.t_baseline = t_baseline

    @staticmethod
    def get_sun_position(times, latitude, longitude, sun_position_method='psa'):
        if sun_position_method == 'psa':
            df = times.to_frame(index=False)
            df.columns = ['time']
            df[['azimuth', 'zenith']] = df['time'].apply(lambda x: sunpos(x, latitude, longitude))
            return df
        else:
            raise ValueError('Invalid argument for sun_position_method variable.')
    
    def compute_sun_position(self, times, latitude, longitude):
        """Computes sun's azimuth and zenith angles for given times and coordinates."""
        sun_positions = self.get_sun_position(times, latitude, longitude)
        return sun_positions
    
    def compute_max_power(self, df, sun_position):
        clearsky_irradiance = df.copy()
        # make the index a column called 'datetime'
        clearsky_irradiance.reset_index(inplace=True)
        clearsky_irradiance['max_power'] = abs(clearsky_irradiance['DNI'] * self.k * (
            1 + self.c * (self.t_baseline - 0)) * (
            np.cos(np.radians(90) - pd.to_numeric(sun_position['zenith'])) *
            np.sin(self.tilt_) *
            np.cos(pd.to_numeric(sun_position['azimuth']) - self.orientation) +
            np.sin(np.radians(90) - pd.to_numeric(sun_position['zenith'])) *
            np.cos(self.tilt_)))
        max_generation = clearsky_irradiance[['datetime', 'max_power']]
        max_generation.columns = ['#time', 'max_generation']
        return max_generation


# (your CSV processing functions)
def load_and_concatenate_csvs(folder):
    df_list = []
    for nested_folder in os.listdir(folder):
        nested_path = os.path.join(folder, nested_folder)
        for file in os.listdir(nested_path):
            if file.endswith('.csv'):
                csv_path = os.path.join(nested_path, file)
                skip = 2
                # open the csv at csv_path using pandas
                df = pd.read_csv(csv_path, skiprows=skip)
                # append the dataframe to df_list
                df_list.append(df)
    df = pd.concat(df_list, ignore_index=True)
    return df


def download_file(url, destination):
    """Download a file from a URL to a given destination."""
    response = requests.get(url)
    with open(destination, 'wb') as file:
        file.write(response.content)


def unzip_file(file_path, destination):
    """Unzip a file to a given destination."""
    with ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination)


def cleanup():
    """Delete temporary files after processing."""
    for filename in os.listdir(SOLAR_DATA_DIR):
        file_path = os.path.join(SOLAR_DATA_DIR, filename)
        os.remove(file_path)

def fetch_download_url(attributes, interval, latitude, longitude, api_key, email, year):
    input_data = {
        'attributes': attributes,
        'interval': interval,
        'to_utc': 'false',
        'wkt': 'POINT({:.4f} {:.4f})'.format(float(longitude), float(latitude)),
        'api_key': api_key,
        'email': email,
        'names': year
    }
    headers = {'x-api-key': api_key}
    response = requests.post(BASE_URL, params=input_data,headers=headers)
    response_data = get_response_json_and_handle_errors(response)
    return response_data['outputs']['downloadUrl']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_script', methods=['POST'])
def execute_script():
    try:
        # (code for extracting form data)
        email = request.form.get('email')
        api_key = request.form.get('api_key')
        years = request.form.getlist('years')
        data_types = request.form.getlist('data_types')
        interval = request.form.get('interval')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')


        # convert data_types to a comma separated string(API requires this)
        attributes = ""
        for data_type in data_types:
            attributes += data_type + ","
        
        for year in years:
            year = str(year)
            year.replace(" ", "")
            download_url = fetch_download_url(attributes, interval, latitude, longitude, api_key, email, year)
            zip_file_path = os.path.join(TEMP_DIR, "solar_data_{}.zip".format(year))
            download_file(download_url, zip_file_path)
            unzip_file(zip_file_path, SOLAR_DATA_DIR)
        
        # (data processing code)
        df = load_and_concatenate_csvs(SOLAR_DATA_DIR)
        df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
        df.drop(['Year', 'Month', 'Day', 'Hour', 'Minute'], axis=1, inplace=True)
        df.set_index('datetime', inplace=True)
        # Compute solar generation using the provided SolarTKMaxPowerCalculator class
        gen_potential = SolarTKMaxPowerCalculator(tilt=34.5, orientation=180, k=1.0)

        sun_position = gen_potential.compute_sun_position(df.index, latitude, longitude)
        max_gen_df = gen_potential.compute_max_power(df, sun_position)

        # Merge the max_generation into the main dataframe
        df = df.merge(max_gen_df, left_index=True, right_on="#time", how="left")
        # rename max_generation
        df.rename(columns={'#time': 'datetime'}, inplace=True)
        df.set_index('datetime', inplace=True)
        df.rename(columns={'max_generation': 'Solar Generation (kWh)'}, inplace=True)
        # cleanup()
        # dump df to csv
        df.to_csv('{}_{}_solar_generation.csv'.format(latitude, longitude), index=True)

        return "Solar data request executed successfully."

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        return error_message
    
def get_response_json_and_handle_errors(response):
    if response.status_code != 200:
        print("An error has occurred with the server or the request. The request response code/status: {} {}".format(response.status_code, response.reason))
        print("The response body: {}".format(response.text))
        exit(1)
    try:
        response_json = response.json()
    except:
        print("The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {}".format(response.text))
        exit(1)
    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print("The request errored out, here are the errors: {}".format(errors))
        exit(1)
    return response_json

if __name__ == "__main__":
    app.run(debug=True)
