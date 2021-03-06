#!/usr/local/sci/bin/python
import os
import datetime
import ColdSurge_forecast_utils as forecast
import json

def main_forecast(date, manage_plots=False):
    print date
    label = 'fcast'
    infolabel = 'MOGREPS_forecast'
    varlist = ['precip', 'u850', 'v850']
    
    # 3. check for forecast data and read
    # For one member deterministic
    #psfiles = forecast.prepare_forecast_data(date, nfcast_days, varlist, label=label, \
    #                                             infolabel=infolabel, debug=True)
    #print psfiles
    
    # for 36 member ensemble
    psfiles = forecast.prepare_forecast_data_ensembles(date, varlist, label=label, \
                                                  infolabel=infolabel, debug=True)
    
    if manage_plots:
        for psfile in psfiles:
            # archives the plots and sends one for display
            
            # save a png copy of the plot for webpage
            # 1. first make a epsi file to remove white space
            os.system('/usr/bin/ps2epsi %s %s.epsi' % (psfile, psfile))
            
            # 2. make a png now
            os.system('/usr/bin/convert -density 100 -antialias %s.epsi %s.png' % (psfile, psfile))
            
            # Copy that to /home/h03/hadpx/configman/MJO/GloSea5_monthly/
            #os.system('cp %s.png /home/h03/hadpx/configman/MJO/MOGREPS_G/' %psfile)
            
            # remove the epsi file
            os.system('rm -f %s.epsi' %psfile)    

    # Write an entry to a json file
    json_file = '/net/home/h03/hadpx/public_html/configman/MJO/MOGREPS_G/filenames.json'

    with open(json_file, mode='r') as feedsjson:
	    feeds = json.load(feedsjson)
	    
    for psfile in psfiles:
	    feeds.append(psfile[psfile.find('_2')+1:])

    with open(json_file, mode='w') as feedsjson:
        json.dump(feeds, feedsjson)		
                
    
if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=2)
    #yesterday = datetime.date(2018, 2, 3)
    #yesterday = today
    
    # Do the MOGREPS bit
    # Copy the plots and publish
    main_forecast(yesterday, manage_plots=True)
    
    
    # Do the analysis
    d1 = datetime.date(2018, 1, 21)  # start date
    d2 = datetime.date(2018, 1, 28)  # end date
    delta = d2 - d1         # timedelta

    for i in range(delta.days + 1):
        date = d1 + datetime.timedelta(days=i)
        #main_forecast(date, manage_plots=True)
