import shutil
import time
from flask import Flask, jsonify, request, render_template
import requests
import pandas as pd
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
DOWNLOAD_URL = {}

class SolarTKMaxPowerCalculator:
    def __init__(self, tilt, orientation, dc_system_size, k=1.0, c=0.05, t_baseline=25):
        self.tilt_ = math.radians(tilt)
        self.orientation = math.radians(orientation)
        self.dc_system_size = dc_system_size
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
        clearsky_irradiance['GTI'] = clearsky_irradiance['DNI'] * abs(
            np.cos(np.radians(self.tilt_) - pd.to_numeric(clearsky_irradiance['Solar Zenith Angle'])) *
            np.sin(self.tilt_) *
            abs(np.cos(pd.to_numeric(sun_position['azimuth']) - self.orientation)) +
            np.sin(np.radians(self.tilt_) - pd.to_numeric(clearsky_irradiance['Solar Zenith Angle'])) *
            np.cos(self.tilt_)) + (clearsky_irradiance['GHI'] - clearsky_irradiance['DNI'] * np.cos(pd.to_numeric(clearsky_irradiance['Solar Zenith Angle'])))
        
        INVERTER_EFFICIENCY = 0.95
        SYSTEM_LOSS = 0.14
        clearsky_irradiance['Solar Generation (kW)'] = self.dc_system_size * (clearsky_irradiance['GTI'] / 1000) * (1-SYSTEM_LOSS) * INVERTER_EFFICIENCY
        clearsky_irradiance['Solar Azimuth Angle'] = sun_position['azimuth']
        max_generation = clearsky_irradiance[['datetime', 'Solar Generation (kW)', 'GTI', 'GHI', 'DNI', 'Solar Azimuth Angle']]
        max_generation.columns = ['#time', 'max_generation', 'gti', 'ghi', 'dni', 'azimuth']
        return max_generation
    
def query_datasets(api_key, latitude, longitude):
    """
    Query the NREL API to find out which datasets are available at the given location by lat & long.
    """
    query_url = "https://developer.nrel.gov/api/nsrdb/v2/data_query.json?"
    params = {
        'api_key': api_key,
        'lat': latitude,
        'lon': longitude
    }
    response = requests.get(query_url, params=params)
    return get_response_json_and_handle_errors(response)


#code from the CSV prcoessing
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
    response = requests.get(url, stream=True)
    with open(destination, 'wb') as dfile:
        for chunk in response.iter_content(chunk_size=10 * 1024):
            dfile.write(chunk)
    # try:
    #     urlretrieve(url, destination)
    # except:
    #     print(url)


def unzip_file(file_path, destination):
    """Unzip a file to a given destination."""
    with ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination)


def cleanup(dir):
    """Delete temporary files after processing."""
    shutil.rmtree(dir)
    print("Temporary files have been cleaned up.")


#take year as an an additional input
def fetch_download_url(dataset_url, attributes, interval, latitude, longitude, year):
    input_data = {
        'attributes': attributes,
        'interval': interval,
        'to_utc': 'false',
        'wkt': 'POINT({:.4f} {:.4f})'.format(longitude, latitude),
        'api_key': api_key,
        'email': email,
        'names': int(year)
    }
    headers = {'x-api-key': api_key}
    # response = requests.post(BASE_URL, input_data, headers=headers)
    response_data = get_response_json_and_handle_errors(requests.post(dataset_url, input_data, headers=headers))
    return response_data['outputs']['downloadUrl']

def download_and_process_data(dataset_url, latitude, longitude, data_types, years, interval, tilt, orientation, dc_system_size):
    all_data_frames = []

    for year in years:
        # year.replace(" ", "")
        # Generate download URL for each year
        download_url = fetch_download_url(dataset_url, data_types, interval, latitude, longitude, year)
        zip_file_path = os.path.join(TEMP_DIR, "solar_data_{}.zip".format(year))
        time.sleep(5)
        download_file(download_url, zip_file_path)
        unzip_file(zip_file_path, SOLAR_DATA_DIR)
        # Load and concatenate CSVs from unzipped data
        data_frame = load_and_concatenate_csvs(SOLAR_DATA_DIR)
        all_data_frames.append(data_frame)
    
    # Combine all data frames into one
    combined_df = pd.concat(all_data_frames, ignore_index=True)
    combined_df = load_and_concatenate_csvs(SOLAR_DATA_DIR)
    combined_df['datetime'] = pd.to_datetime(combined_df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
    combined_df.drop(['Year', 'Month', 'Day', 'Hour', 'Minute'], axis=1, inplace=True)
    combined_df.set_index('datetime', inplace=True)
    
    # Compute solar generation using the provided SolarTKMaxPowerCalculator class
    gen_potential = SolarTKMaxPowerCalculator(tilt=34.5, orientation=180, dc_system_size=25)
    sun_position = gen_potential.compute_sun_position(combined_df.index, latitude, longitude)
    max_gen_df = gen_potential.compute_max_power(combined_df, sun_position)
    # Merge the max_generation into the main dataframe
    combined_df = combined_df.merge(max_gen_df, left_index=True, right_on="#time", how="left")
    # rename max_generation
    combined_df.rename(columns={'#time': 'datetime'}, inplace=True)
    combined_df.set_index('datetime', inplace=True)
    combined_df.rename(columns={'max_generation': 'Solar Generation (kW)'}, inplace=True)
    return combined_df

def generate_csv_url(csv_path):
    return F"{TEMP_DIR}/{csv_path}"

# (your Flask routes)
email = ""
api_key = ""
latitude = ""
longitude = ""

@app.route('/')
def input_coordinates():
    return render_template('input.html')


@app.route('/get_available_datasets', methods=['POST'])
def get_available_datasets():
    global email, api_key, latitude, longitude

    email = request.form.get('email')
    api_key = request.form.get('api_key')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if not latitude or not longitude:
        return render_template('error.html', error_message="Invalid Latitude and/or Longitude")

    wkt = f'POINT({longitude} {latitude})'

    NREL_API_URL = f'https://developer.nrel.gov/api/solar/nsrdb_data_query.json?api_key={api_key}'

    params = {
        'wkt': wkt,
    }

    try:
        # Make the GET request to the NREL API
        response = requests.get(NREL_API_URL, params=params)
        response.raise_for_status()  # raise an exception if the request fails
        
        data = response.json()

        # Extract dataset options from the response and turn into an array of dataset names
        # as you extact the years you should also give eacch year its respective urls as a key value pair (just an idea)
        dataset_options = [dataset['displayName'] for dataset in data.get('outputs', [])]
        years = [dataset['availableYears'] for dataset in data.get('outputs')]
        intervals = [dataset['availableIntervals'] for dataset in data.get('outputs', [])]

        for dataset in data.get('outputs'):
            if isinstance(dataset['availableYears'][0], int):
                for link in dataset['links']:
                    DOWNLOAD_URL[link['year']] = link['link']
        
        return render_template('index.html', dataset_options=dataset_options, years=years, intervals=intervals)
    
    except requests.RequestException as e:
        return render_template('error.html', error_message=str(e))

# Alter the fetch_download_url function to accept a dataset parameter
@app.route('/run_script', methods=['POST'])
def execute_script(): 
    try:
        dataset = request.form.get('dataset')
        years = request.form.getlist('years')
        data_types = request.form.getlist('data_types')
        interval = request.form.get('interval')

        # convert data_types to a comma separated string(API requires this)
        attributes = ""
        for data_type in data_types:
            attributes += data_type + ","

        # add ghi, dni, solar zenith angle, and temperature to attributes
        attributes += "ghi,dni,solar_zenith_angle,air_temperature"

        #if you are choosing multiple years then the link for each year will need to be adjusted
        for year in years:
            year = str(year)
            year.replace(" ", "")
            # Generate download URL for each year
            url = DOWNLOAD_URL[year]

            download_url = fetch_download_url(url, attributes, interval, latitude, longitude, year)
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
        return render_template('error.html', error_message=str(e)) 
    
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
