# from flask import Flask, request, render_template, jsonify
# import requests
# import pandas as pd
# import urllib.parse
# import time
# import config

# app = Flask(__name__)

# # Define your constants
# BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.json?"
# POINTS = ['2277372']

# def run_nrel_script(years, data_types, interval, latitude, longitude, email, api_key):
#     try:
#         input_data = {
#             'attributes': ','.join(data_types),
#             'interval': interval,
#             'to_utc': 'false',
#             'wkt': 'POINT({:.4f} {:.4f})'.format(float(longitude), float(latitude)),
#             'api_key': api_key,
#             'email': email,
#         }

#         for year in years.split(','):
#             print(f"Processing year: {year}")
#             for id, location_ids in enumerate(POINTS):
#                 input_data['names'] = [int(year)]
#                 print(f'Making request for point group {id + 1} of {len(POINTS)}...')

#                 if '.csv' in BASE_URL:
#                     url = BASE_URL + urllib.parse.urlencode(data, True)
#                     data = pd.read_csv(url)
#                     print(f'Response data (you should replace this print statement with your processing): {data}')
#                 else:
#                     headers = {
#                         'x-api-key': api_key
#                     }
#                     response = requests.post(BASE_URL, input_data, headers=headers)
#                     response_json = get_response_json_and_handle_errors(response)
#                     download_url = response_json['outputs']['downloadUrl']
#                     print(response_json['outputs']['message'])
#                     print(f"Data can be downloaded from this URL when ready: {download_url}")

#                     # Delay for 1 second to prevent rate limiting
#                     time.sleep(1)
#                 print(f'Processed')

#         return "Script executed successfully. You can display the results here."

#     except Exception as e:
#         error_message = f"An error occurred: {str(e)}"
#         return error_message

# def get_response_json_and_handle_errors(response: requests.Response) -> dict:
#     if response.status_code != 200:
#         error_message = f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}"
#         error_message += f"\nThe response body: {response.text}"
#         raise Exception("Request to the server failed.")

#     try:
#         response_json = response.json()
#     except:
#         error_message = f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}"
#         raise Exception("Response couldn't be parsed as JSON.")

#     if len(response_json['errors']) > 0:
#         errors = '\n'.join(response_json['errors'])
#         error_message = f"The request errored out, here are the errors: {errors}"
#         raise Exception(f"Request errors: {errors}")

#     return response_json

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/run_script', methods=['POST'])
# def execute_script():
#     try:
#         email = request.form.get('email')
#         api_key = request.form.get('api_key')
#         years = request.form.get('years')
#         data_types = request.form.getlist('data_types')
#         interval = request.form.get('interval')
#         latitude = request.form.get('latitude')
#         longitude = request.form.get('longitude')

#         result = run_nrel_script(years, data_types, interval, latitude, longitude, email, api_key)

#         return result

#     except Exception as e:
#         error_message = f"An error occurred: {str(e)}"
#         return error_message

# if __name__ == "__main__":
#     app.run(debug=True)










