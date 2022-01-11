#!/net/project/ukmo/scitools/opt_scitools/environments/default/2020_10_12/bin/python
import sys, os

import numpy as np

sys.path.append('/home/h03/hadpx/MJO/Monitoring/mogreps_cold_surge')
import os
import datetime
from src import retrieve_mogreps_data as retrieve_mogreps
from src import retrieve_mogreps_profile_deterministic as rmpd
from src import plot_ColdSurge_profiles
from src import ColdSurge_forecast_utils as forecast
from src import html_generator
from src import html_generator_profiles


def main_forecast(forecast_date_time):
    print(forecast_date_time)

    '''
    # 1. retrieve mogreps data
    retrieve_mogreps.retrieve_mogreps_forecast_data(forecast_date_time)

    # 2. process precip data to 24 hr values and save as a
    # combined file for all lead times and members
    # for the ease of probability computations
    retrieve_mogreps.prepare_24hr_precip_accum(forecast_date_time)

    # 3. Process wind data, very straightforward
    retrieve_mogreps.prepare_24hr_wind(forecast_date_time, varname='x_wind', level=850)
    retrieve_mogreps.prepare_24hr_wind(forecast_date_time, varname='y_wind', level=850)

    # 3. check for forecast data and read
    # plot ensemble mean plots
    forecast.plot_forecast_ensemble_mean(forecast_date_time)

    # 4. Plot forecast probability maps for thresholds
    forecast.plot_forecast_probability(forecast_date_time,
                                       precip_thresholds=[10, 20, 30],
                                       speed_thresholds=[5, 10, 15])
    '''

    # 5. retrieve profile data
    rmpd.retrieve_mogreps_determin_profile(forecast_date_time)

    #6. Plot cold surge profiles
    plot_ColdSurge_profiles.plot_maps_profiles(forecast_date_time, varname='relative_humidity',
                                               map_level=700, clevels=np.arange(0, 110, 10))
    plot_ColdSurge_profiles.plot_maps_profiles(forecast_date_time, varname='x_wind',
                                               map_level=850, clevels=np.arange(-10, 10, 2))
    plot_ColdSurge_profiles.plot_maps_profiles(forecast_date_time, varname='y_wind',
                                               map_level=850, clevels=np.arange(-10, 10, 2))

    # 5. Generate a html file
    #html_generator.write_html_page_instantaneous(forecast_date_time)
    print(forecast_date_time)
    html_generator_profiles.write_html_page_instantaneous(forecast_date_time, varname='relative_humidity')

if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Hours have to be either 00Z or 12Z
    #yesterday = datetime.datetime(yesterday.year,
    #                              yesterday.month,
    #                              yesterday.day, 12)

    yesterday = datetime.datetime(2021, 9, 25, 00)

    # Do the MOGREPS bit
    # Copy the plots and publish
    main_forecast(yesterday)

    ''' 
    # Do the analysis
    d1 = datetime.date(2018, 1, 01)  # start date
    d2 = datetime.date(2018, 1, 31)  # end date
    delta = d2 - d1         # timedelta

    for i in range(delta.days + 1):
        date = d1 + datetime.timedelta(days=i)
        main_forecast(date, manage_plots=True)
    '''
