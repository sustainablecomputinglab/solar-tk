import requests
import pandas as pd
import urllib.parse
import time
import config

import requests
import pandas as pd
import urllib.parse
import time
import config
import shutil
import os
import numpy as np
#ghi dni and solar zenith  and temperature are in requests 

BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.json?"
POINTS = ['2277372']
TEMP_DIR = 'temp_data'  # Defined a temporary directory

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)  # Create the temporary directory if it doesn't exist


def cleanup():
    """Delete temporary files after processing."""
    shutil.rmtree(TEMP_DIR)
    print("Temporary files have been cleaned up.")

def main():
    # Get user input for the years of data
    years = input("Enter the year(s) for which you want data (e.g., 2021): ")
    # You can add validation here to check if the input is valid

    # Get user input for data types
    data_types = input("Enter data types separated by commas (e.g., ghi,dni,dew_point): ").split(',')
    # You can split the input into a list of data types

    # Get user input for the interval
    interval = input("Enter the data interval (5, 15, 30, or 60 minutes): ")
    # You can add validation here to check if the input is valid

    # Get user input for latitude and longitude
    latitude = float(input("Enter the latitude: "))
    longitude = float(input("Enter the longitude: "))
    
    input_data = {
        'attributes': ','.join(data_types),
        'interval': interval,
        'to_utc': 'false',
        'wkt': 'POINT({:.4f} {:.4f})'.format(longitude, latitude),
        'api_key': config.API_KEY,
        'email': config.EMAIL,
    }

    for year in years.split(','):
        print(f"Processing year: {year}")
        for id, location_ids in enumerate(POINTS):
            input_data['names'] = [int(year)]
            print(f'Making request for point group {id + 1} of {len(POINTS)}...')

            if '.csv' in BASE_URL:
                url = BASE_URL + urllib.parse.urlencode(data, True)
                data = pd.read_csv(url)

                # Compute Solar Elevation Angle
                data['Solar Elevation Angle'] = 90 - data['solar_zenith']

                # Compute GTI using the DNI and DHI irradiance values
                data['GTI'] = data['DNI'] * np.sin(np.radians(data['Solar Elevation Angle'])) + data['DHI']

                # Hardcoded values
                PANEL_TILT = 34.5  # degrees
                dc_system_size = 25.0  # kW
                INVERTER_EFFICIENCY = 0.95
                SYSTEM_LOSS = 0.14

                # Convert GTI to kW and apply the system size, loss, and inverter efficiency factors
                data['Solar Generation (kW)'] = dc_system_size * (data['GTI'] / 1000) * (1 - SYSTEM_LOSS) * INVERTER_EFFICIENCY

                print(f'Response data (you should replace this print statement with your processing): {data}')
            else:
                headers = {
                  'x-api-key': config.API_KEY
                }
                data = get_response_json_and_handle_errors(requests.post(BASE_URL, input_data, headers=headers))
                download_url = data['outputs']['downloadUrl']
                print(data['outputs']['message'])
                print(f"Data can be downloaded from this URL when ready: {download_url}")

                # Delay for 1 second to prevent rate limiting
                time.sleep(1)
            print(f'Processed')

        cleanup()


def get_response_json_and_handle_errors(response: requests.Response) -> dict:
    if response.status_code != 200:
        print(f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
        print(f"The response body: {response.text}")
        exit(1)
    
    try:
        response_json = response.json()
    except:
        print(f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
        exit(1)

    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print(f"The request errored out, here are the errors: {errors}")
        exit(1)
    return response_json

if __name__ == "__main__":
    main()