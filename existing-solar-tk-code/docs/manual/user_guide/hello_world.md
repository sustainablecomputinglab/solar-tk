# Using Historical Data [existing solar sites]

**Step 1**. The standard approach is to use the Solar-TK pipeline with some historical generation data at the start to estimate the physical parameters. You can use the physical parameter module as following. 

```bash
./path_to_solar-tk/solartk/parameters.py latitude longitude historical_data.csv
```

Here, latitude and longitude are the coordinates of the solar site. The historical data file uses the CSV format with first column containing local time and the sceond column contains solar generation in kW. The file should have a header with first column named "time" and second column named "solar". 

The output of the module would be the following. 

```bash
latitude longitude module_area tilt orientation temperature_coefficient baseline_temperature
```

We have provided data from an example site in the data folder. You can run the following command to find the paramaters for the example home. 

```bash
./path_to_solar-tk/solartk/parameters.py 42 -72 path_to_solar-tk/data/example_home_days.csv 
```

* please replace the "path_to_solar-tk" based on where you have placed the solar-tk folder. 

**Step 2**. The second module in the Solar-TK pipeline is the maximum generation module. You can pipe the output of the parameters module to the maximum generation module. The standard command is given below.  

```bash
./path_to_solar-tk/solartk/parameters.py latitude longitude historical_data.csv| ./path_to_solar-tk/solartk/max_generation.py start_time end_time resolution
```

Here, the start_time and end_time are the start and end timestamps of the time period for which you want to model your site. The format of these dates is "yyyy-mm-dd HH:MM:SS". The resolution is the granularity of the time series data in seconds. 

Keep in mind that our toolkit uses temperature data from weather underground (WU), which provides only hourly temperature data. 

This module would output the coordinates of the site and a time series. The time series will have local time as the first column and maximum solar generation in watts as the second column. 

For the example home, the command is given below. 

```bash
./path_to_solar-tk/solartk/parameters.py 42 -72 path_to_solar-tk/data/example_home_days.csv| ./path_to_solar-tk/solartk/max_generation.py '2015-01-02 00:00:00' '2015-01-02 23:00:00' '3600' 
```

The output of the module is given below. 

```bash
#latitude(°),longitude(°)
42,-72
#time,max_generation
2015-01-02 00:00:00,-0.0
2015-01-02 01:00:00,-0.0
2015-01-02 02:00:00,-0.0
2015-01-02 03:00:00,-0.0
2015-01-02 04:00:00,-0.0
2015-01-02 05:00:00,-0.0
2015-01-02 06:00:00,-0.0
2015-01-02 07:00:00,0.0
2015-01-02 08:00:00,821.1492425415427
2015-01-02 09:00:00,3197.3524125028844
2015-01-02 10:00:00,5054.168383824413
2015-01-02 11:00:00,6354.087812689646
2015-01-02 12:00:00,6915.632712663597
2015-01-02 13:00:00,6768.873078917656
2015-01-02 14:00:00,5840.8589804359335
2015-01-02 15:00:00,3976.750549629417
2015-01-02 16:00:00,785.0225410518235
2015-01-02 17:00:00,0.0
2015-01-02 18:00:00,0.0
2015-01-02 19:00:00,-0.0
2015-01-02 20:00:00,-0.0
2015-01-02 21:00:00,-0.0
2015-01-02 22:00:00,-0.0
2015-01-02 23:00:00,-0.0
```

**Step 3**. The third step is to incorporate the weather effects on to the maximum generation output. The command to use the weather-adjustement module is given below. 

```bash
./path_to_solar-tk/solartk/parameters.py latitude longitude historical_data.csv| ./path_to_solar-tk/solartk/max_generation.py start_time end_time resolution |./path_to_solar-tk/solartk/weather_adjusted.py
```
This module would output a time series with local time as the first column and weather adjusted solar generation in watts as the second column. 

Keep in mind that our toolkit uses weather data from weather underground (WU), which provides only hourly temperature data. Therefore, the same cloud cover and temperature values are used if the required resolution is less than one hour. 

For the example home, the command is given below. 

```bash
./path_to_solar-tk/solartk/parameters.py 42 -72 path_to_solar-tk/data/example_home_days.csv| ./path_to_solar-tk/solartk/max_generation.py '2015-01-02 00:00:00' '2015-01-02 23:00:00' '3600'| ./path_to_solar-tk/solartk/weather_adjusted.py
```

The output of the module is given below. 

```bash
#time,adjusted_generation
2015-01-02 00:00:00,-0.0
2015-01-02 01:00:00,-0.0
2015-01-02 02:00:00,-0.0
2015-01-02 03:00:00,-0.0
2015-01-02 04:00:00,-0.0
2015-01-02 05:00:00,-0.0
2015-01-02 06:00:00,-0.0
2015-01-02 07:00:00,0.0
2015-01-02 08:00:00,207.71285707124488
2015-01-02 09:00:00,472.59242880598487
2015-01-02 10:00:00,5531.387587109255
2015-01-02 11:00:00,3934.6846851124933
2015-01-02 12:00:00,1689.7622527409383
2015-01-02 13:00:00,7086.493607989304
2015-01-02 14:00:00,6392.495239973352
2015-01-02 15:00:00,4303.845369356131
2015-01-02 16:00:00,837.8836998431423
2015-01-02 17:00:00,0.0
2015-01-02 18:00:00,0.0
2015-01-02 19:00:00,-0.0
2015-01-02 20:00:00,-0.0
2015-01-02 21:00:00,-0.0
2015-01-02 22:00:00,-0.0
2015-01-02 23:00:00,-0.0
```

# Without Historical Data [new solar sites]
**Step 1**. In this case, the user is supposed to know the parameters. The first step of the traditional pipeline will be skipped. The user will need to provide the physical paramaters of the module to the maximum generation module directly. 

**Step 2**. In this case, the command to use the maximum generation module would be the following. 

```bash
./path_to_solar-tk/solartk/max_generation.py start_time end_time resolution latitude longitude module_area tilt orientation temperature_coefficient baseline_temperature
```
Here, the different variables are
* start_time: start time of the period of interest in the "yyyy-mm-dd HH:MM:SS" format. 
* end_time: end time of the period of interest in the "yyyy-mm-dd HH:MM:SS" format.  
* resolution: the granularity of the output data in seconds
* module_area: the surface area of the solar panels in m^2 from the solar panel datasheet. 
* tilt: tilt of the surface where the solar panels will be installed in degrees. A good value would be the latitude angle if not sure about the tilt of the surface.  
* orientation: orientation of the surface where solar panels will be installed in degrees. A good value would be the 180 for northere hemisphere. 
* temperature_coefficient: a parameter quantifying the effect of temperature on the solar panel. Solar modules typically have a value of 0.005. 
*  baseline_temperature: the temperature where the maximum power would be viewed. A good guess would be 0 degree celsius. 

Please refer to the step 2 in the "Using Historical Data" for the output format and the output for the example home. 

**Step 3**. The third step is to incorporate the weather effects on to the maximum generation output. The command to use the weather-adjustement module is given below. 

```bash
./path_to_solar-tk/solartk/max_generation.py start_time end_time resolution latitude longitude module_area tilt orientation temperature_coefficient baseline_temperature| ./path_to_solar-tk/solartk/weather_adjusted.py
```

Please refer to the step 3 in the "Using Historical Data" for the output format and the output for the example home. 