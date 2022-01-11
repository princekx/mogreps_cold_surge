import os
import datetime
import MOGREPS_ColdSurge_monitor

if __name__ == '__main__':
    #today = datetime.date.today()
    #yesterday = today - datetime.timedelta(days=1)
    #yesterday = datetime.date(2018, 2, 3)
    #yesterday = today
    
    # Do the MOGREPS bit
    # Copy the plots and publish
    #main_forecast(yesterday, manage_plots=True)
    
    
    # Do the analysis
    d1 = datetime.datetime(2021, 11, 26, 12)  # start date
    d2 = datetime.datetime(2021, 12, 6, 12)  # end date
    delta = d2 - d1         # timedelta

    for i in range(delta.days + 1):
        fcdate = d1 + datetime.timedelta(days=i)
        MOGREPS_ColdSurge_monitor.main_forecast(fcdate)
