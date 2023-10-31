import datetime
import pandas as pd 
from helpers import granularity_to_freq
import time
import numpy as np 

rad = np.pi/180
dEarthMeanRadius = 6371.01
dAstronomicalUnit = 149597890

def get_sun_position(start_time=None, end_time=None, granularity=None, latitude=None, longitude=None, sun_position_method='psa'):

    if (sun_position_method=='psa'):

        # create a pandas datetimeindex 
        df = pd.date_range(start_time, end_time, freq=granularity_to_freq(granularity))

        # convert it into a simple dataframe and rename the column
        df = df.to_frame(index=False)
        df.columns = ['time']

        # call sunpos function for each time to get sun azimuth and zenith angles
        df[['sun_azimuth', 'sun_zenith']] = df['time'].apply(lambda x: sunpos(x, latitude, longitude))
        
        return df

    else: 
        raise ValueError('Invalid argument for sun_position_method variable.')

def sunpos(udtTime, latitude, longitude):
        # Calculate difference in days between the current Julian Day 
        # and JD 2451545.0, which is noon 1 January 2000 Universal Time

        # Calculate time of the day in UT decimal hours
        dDecimalHours = udtTime.hour + (udtTime.minute + udtTime.second/60)/60
        # Calculate current Julian Day
        liAux1 =(udtTime.month-14)/12
        liAux2=(1461*(udtTime.year + 4800 + liAux1))/4 + (367*(udtTime.month 
                - 2-12*liAux1))/12- (3*((udtTime.year + 4900 + liAux1)/100))/4+udtTime.day-32075
        dJulianDate=(liAux2)-0.5+dDecimalHours/24.0
        # Calculate difference between current Julian Day and JD 2451545.0 
        dElapsedJulianDays = dJulianDate-2451545.0



        # Calculate ecliptic coordinates (ecliptic longitude and obliquity of the 
        # ecliptic in radians but without limiting the angle to be less than 2*Pi 
        # (i.e., the result may be greater than 2*Pi)
        dOmega=2.1429-0.0010394594*dElapsedJulianDays
        dMeanLongitude = 4.8950630+ 0.017202791698*dElapsedJulianDays # Radians
        dMeanAnomaly = 6.2400600+ 0.0172019699*dElapsedJulianDays
        dEclipticLongitude = (dMeanLongitude + 0.03341607*np.sin(dMeanAnomaly) 
                            + 0.00034894*np.sin(2*dMeanAnomaly)
                            -0.0001134 -0.0000203*np.sin(dOmega))
        dEclipticObliquity = 0.4090928 - 6.2140e-9*dElapsedJulianDays+0.0000396*np.cos(dOmega)

        # Calculate celestial coordinates ( right ascension and declination ) in radians 
        # but without limiting the angle to be less than 2*Pi (i.e., the result may be 
        # greater than 2*Pi)
        dSin_EclipticLongitude= np.sin(dEclipticLongitude)
        dY = np.cos(dEclipticObliquity) * dSin_EclipticLongitude
        dX = np.cos(dEclipticLongitude)
        dRightAscension = np.arctan2(dY,dX)
        if( dRightAscension < 0.0 ): 
            dRightAscension = dRightAscension + 2*np.pi
        dDeclination = np.arcsin( np.sin( dEclipticObliquity )*dSin_EclipticLongitude )



        # Calculate local coordinates ( azimuth and zenith angle ) in degrees
        dGreenwichMeanSiderealTime = 6.6974243242 + 0.0657098283*dElapsedJulianDays + dDecimalHours
        dLocalMeanSiderealTime = (dGreenwichMeanSiderealTime*15 
            + longitude)*rad
        dHourAngle = dLocalMeanSiderealTime - dRightAscension
        dLatitudeInRadians = np.radians(latitude)
        dCos_Latitude = np.cos(dLatitudeInRadians)
        dSin_Latitude = np.sin(dLatitudeInRadians)
        dCos_HourAngle= np.cos(dHourAngle)
        ZenithAngle = (np.arccos(dCos_Latitude*dCos_HourAngle* np.cos(dDeclination) + np.sin(dDeclination)*dSin_Latitude))
        dY = -np.sin(dHourAngle)
        dX = np.tan(dDeclination)*dCos_Latitude - dSin_Latitude*dCos_HourAngle
        Azimuth = np.arctan2(dY,dX)
        if (Azimuth < 0.0): 
            Azimuth = Azimuth + 2*np.pi
        Azimuth = Azimuth/rad
        # Parallax Correction
        dParallax=(dEarthMeanRadius/dAstronomicalUnit)*np.sin(ZenithAngle)
        ZenithAngle=(ZenithAngle + dParallax)/rad

        return pd.Series([np.radians(Azimuth), np.radians(ZenithAngle)])


# if __name__ == "__main__":
#     start_time_ = datetime.datetime(year=2018, month=1, day=1, hour=0, minute=0, second=0)
#     end_time_ = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0)

#     start_ = time.time()
#     get_sun_position(start_time=start_time_, end_time=end_time_,granularity=3600, latitude=42, longitude=-72)
#     print(time.time()-start_)