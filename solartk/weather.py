import datetime
import time
import pytz
import pandas as pd
import json
import urllib.request
import requests
# from tzwhere import tzwhere
# from darksky import forecast
import numpy as np

from helpers import okta_to_percent, granularity_to_freq


def get_temperature_cloudcover(
    start_time=None,
    end_time=None,
    granularity=None,
    latitude=None,
    longitude=None,
    source="weather_underground",
    timezone="US/Eastern",
    darksky_api_key=None,
):
    if source == "weather_underground" or darksky_api_key == None:
        # create a pandas datetimeindex
        df = pd.date_range(start_time - datetime.timedelta(days=1), end_time, freq="D")

        # convert it into a simple dataframe and rename the column
        df = df.to_frame(index=False)
        df.columns = ["time"]

        # convert it into required format for weather underground
        df["time"] = df["time"].dt.strftime("%Y%m%d")

        temp_cloud_df = pd.DataFrame()

        for _, row in df.iterrows():
            # print(row['time'])
            try:
                url = "https://api.weather.com/v1/geocode/{}/{}/observations/historical.json?apiKey=e1f10a1e78da46f5b10a1e78da96f525&startDate={}&endDate={}&units=e".format(
                    latitude, longitude, row["time"], row["time"]
                )
                data = urllib.request.urlopen(url).read()
                output = json.loads(data)
                output = pd.DataFrame(output["observations"])
                output = output[["valid_time_gmt", "temp", "clds", "wx_phrase"]]
                output.columns = ["time", "temperature", "clds", "wx_phrase"]
                temp_cloud_df = pd.concat([temp_cloud_df, output], ignore_index=True)
            except urllib.error.HTTPError as e:
                pass
            # time.sleep(0.01)

        # convert to datetime and set the correct timezone
        temp_cloud_df["time_s"] = temp_cloud_df["time"]
        temp_cloud_df["time"] = (
            pd.to_datetime(temp_cloud_df["time"], unit="s")
            .dt.tz_localize("utc")
            .dt.tz_convert(timezone)
        )
        # temp_cloud_df['time'] = temp_cloud_df['time'].dt.round("H")

        # resample the data to desired granularity
        temp_cloud_df = temp_cloud_df.set_index(temp_cloud_df["time"])
        temp_cloud_df = temp_cloud_df.resample(granularity_to_freq(granularity)).ffill()
        temp_cloud_df = temp_cloud_df[["temperature", "clds"]]
        temp_cloud_df = temp_cloud_df.reset_index()

        # chnage to C from F
        temp_cloud_df["temperature"] = (temp_cloud_df["temperature"] - 32) * 5 / 9

        # cloud okta code to percent
        temp_cloud_df["clouds"] = pd.to_numeric(
            temp_cloud_df["clds"].apply(lambda x: okta_to_percent(x))
        )

        # keep only relevant columns
        temp_cloud_df = temp_cloud_df[["time", "temperature", "clouds", "clds"]]

        ######################### future release ############################
        # # create a pandas datetimeindex
        # df = pd.date_range(start_time, end_time, freq=granularity_to_freq(granularity), tz=timezone)

        # # convert it into a simple dataframe and rename the column
        # df = df.to_frame(index=False)
        # df.columns = ['time']

        # # combine both df and temperature_df
        # temp_cloud_df = df.join(temp_cloud_df.set_index('time'), on='time')
        ####################################################################

        # temp_cloud_df['time'] = temp_cloud_df['time'].dt.tz_localize('utc').dt.tz_convert(timezone)
        temp_cloud_df["time"] = temp_cloud_df["time"].dt.tz_localize(None)

        # print(temp_cloud_df)

    elif source == "darksky" and darksky_api_key != None:
        time = []
        temperature = []
        cloudcover = []
        summary = []

        # localizing the datetime based on the timezone
        start: datetime.datetime = timezone.localize(start_time)
        end: datetime.datetime = timezone.localize(end_time)

        while start <= end:
            day = int(start.timestamp())
            start = start + datetime.timedelta(days=1)

            response = urllib.request.urlopen(
                "https://api.darksky.net/forecast/{}/{},{},{}?exclude=currently,daily,flags".format(
                    darksky_api_key, latitude, longitude, day
                )
            ).read()
            output = json.loads(response)["hourly"]["data"]

            for item in output:
                time.append(item["time"])
                temperature.append(item["temperature"])
                cloudcover.append(item["cloudCover"])
                summary.append(item["summary"])

        temp_cloud_df = pd.DataFrame(
            {
                "time": time,
                "temperature": temperature,
                "clouds": cloudcover,
                "clds": summary,
            }
        )
        temp_cloud_df["time"] = (
            pd.to_datetime(temp_cloud_df["time"], unit="s")
            .dt.tz_localize("utc")
            .dt.tz_convert(timezone)
            .dt.tz_localize(None)
        )
        temp_cloud_df["temperature"] = (temp_cloud_df["temperature"] - 32) * 5 / 9

    else:
        print("Sorry, {} source has not been implemented yet.".format(source))

    return temp_cloud_df


if __name__ == "__main__":
    data = get_temperature_cloudcover(
        start_time=datetime.datetime(2019, 1, 1, 0),
        end_time=datetime.datetime(2019, 1, 2, 0),
        granularity=3600,
        latitude=42,
        longitude=-72,
        source="weather_underground",
        timezone="US/Eastern",
        darksky_api_key=None,
    )
    print(data)
