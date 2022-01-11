#!/usr/local/sci/bin/python
import os, sys
import glob
import iris
import matplotlib
# use the Agg environment to generate an image rather than outputting to screen
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import iris.plot as iplt
import cartopy.crs as ccrs
import datetime 
import numpy as np
import data_paths

def prepare_forecast_data(date, varlist, label=None, infolabel=None, debug=True):
    # Cold surge identification
    chang_box = [107, 115, 5, 10]        # CP Chang's 2nd domain
    
    # Hattori box for cross equatorial surges
    hattori_box = [105, 115, -5, 5]
    
    Chang_threshold = 9.0 # 10 # wind speed m/s
    Hattori_threshold = -2.0 # m/s meridional wind
    
    # Prepare glosea data
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    fcast_out_dir = data_paths.dirs('mog_forecast_out_dir')
    anal_out_dir = data_paths.dirs('analy_out_dir')
    plot_ens_dir = data_paths.dirs('plot_ens')
            
    datelabel = '%s/%s/%s' % (date.year, str('%02d' % date.month), str('%02d' % date.day))
    yyyymmdd_datelabel = '%s%s%s' % (date.year, str('%02d' % date.month), str('%02d' % date.day))
    
    
    filequery = fcast_in_dir + '/%s/*' % (datelabel)
    
    files_members = glob.glob(filequery)
    files_members.sort()
    
    mems = [memb[-3:] for memb in files_members]
    mems = ['000']
    print mems
    
    #mems = len(mems)
    for n, ens in enumerate(mems):
        filequery = files_members[n] + '/*.pp'
        data_files = glob.glob(filequery)
        data_files.sort()
        
        if not data_files:
            print 'ERROR IN _prepare_forecast_data!!!'
            print '%s files not found in %s for %s' % (infolabel, fcast_in_dir, date)
            sys.exit()
            
        xcubes = iris.load_cube(data_files, 'toa_outgoing_longwave_flux')
        prec_cubes = xcubes.copy()
        ntime, nlat, nlon = prec_cubes.shape
        print ntime
        for i in range(1, ntime):
            prec_cubes.data[i - 1] = (xcubes.data[i] - xcubes.data[i - 1]) / 24.
            print np.min(prec_cubes[i - 1].data), np.max(prec_cubes[i - 1].data)
            
        u850_cubes = iris.load_cube(data_files, 'x_wind')
        u850_cubes = u850_cubes.extract(iris.Constraint(pressure=850))
        
        v850_cubes = iris.load_cube(data_files, 'y_wind')
        v850_cubes = v850_cubes.extract(iris.Constraint(pressure=850))
        
        # subset forecast data and append to analysis
        prec_cubes = prec_cubes.intersection(latitude=(-11, 21), longitude=(89, 131))
        u850_cubes = u850_cubes.intersection(latitude=(-11, 21), longitude=(89, 131))
        v850_cubes = v850_cubes.intersection(latitude=(-11, 21), longitude=(89, 131))
        print u850_cubes
        
        
        
        #fig, axes = plt.subplots(2, 2, figsize=(10,5))
        psfiles = []
        for i in range(ntime - 1):
            
            fig = plt.figure(figsize=(10, 10), dpi=100)
            
            prec = prec_cubes[i]
            u850 = u850_cubes[i]
            v850 = v850_cubes[i]
            speed = u850.copy()
            speed.data = np.sqrt(u850.data ** 2 + v850.data ** 2)
            
            # box averages
            u850_ba = u850.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            u850_ba = u850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            v850_ba = v850.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            v850_ba = v850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            speed_ba = speed.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            speed_ba = speed_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            print u850_ba.data, v850_ba.data, speed_ba.data
            
            xlon = u850.coord('longitude').points
            ylat = u850.coord('latitude').points
            lw = 3 * speed.data / speed.data.max()
            
            
            cf = iplt.contourf(prec, levels=range(40, 240, 20), cmap='gray', alpha=0.75)
            axc = plt.gca()
            axc.coastlines('50m')
            axc.set_ylim([-10, 20])
            axc.set_xlim([90, 130])
            axc.stock_img()
            axc.set_yticks([-10, 0, 10, 20], crs=ccrs.PlateCarree())
            axc.set_xticks([90, 100, 110, 120, 130], crs=ccrs.PlateCarree())
            axc.gridlines()
            
            plt.title('prec, 850hPa winds \n Forecast start: %s, Lead: T+%s h' % (datelabel, (i * 24)))
            cl = plt.gca().streamplot(xlon, ylat, u850.data, v850.data, density=(2., 2.), color=speed.data, linewidth=lw)
            
            colorbar_axes = plt.gcf().add_axes([0.2, 0.15, 0.6, 0.025])
            colorbar = plt.colorbar(cf, colorbar_axes, orientation='horizontal')

            colorbar_axes = plt.gcf().add_axes([0.92, 0.25, 0.025, 0.5])
            colorbar = plt.colorbar(cl.lines, colorbar_axes, orientation='vertical')
            
            
            # Check for cross-equatorial surges
            if speed_ba.data >= Chang_threshold and u850_ba.data < 0 and v850_ba.data < 0:
                
                print 'Cold surge detected!!!'
                font = {'color':  'darkorange', 'weight': 'bold', 'size': 16}
                axc.text(90, 21.5, 'COLD SURGE!', fontdict=font)
                    
                v850_hattori = v850.intersection(latitude=(hattori_box[2], hattori_box[3]), longitude=(hattori_box[0], hattori_box[1]))
                v850_hattori = v850_hattori.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
                if v850_hattori.data <= Hattori_threshold:
                    print 'Cross-Equatorial Cold surge detected!!!'
                    font = {'color':  'red', 'weight': 'bold', 'size': 16}
                    axc.text(90, 19., 'CROSS-EQUATORIAL SURGE!!', fontdict=font)
            
            
            psfile = os.path.join(plot_ens_dir, 'Cold_surge_monitor', 'Cold_surge_monitor_%s_T%sh.ps' % (yyyymmdd_datelabel, (i * 24)))
            psfiles.append(psfile)
            plt.savefig(psfile)
        return psfiles

def prepare_forecast_data_ensembles(date, varlist, label=None, infolabel=None, debug=True):
    # Cold surge identification
    chang_box = [107, 115, 5, 10]        # CP Chang's 2nd domain
    
    # Hattori box for cross equatorial surges
    hattori_box = [105, 115, -5, 5]
    
    Chang_threshold = 9.0 # 10 # wind speed m/s
    Hattori_threshold = -2.0 # m/s meridional wind
    
    # Prepare glosea data
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    fcast_out_dir = data_paths.dirs('mog_forecast_out_dir')
    anal_out_dir = data_paths.dirs('analy_out_dir')
    plot_ens_dir = data_paths.dirs('plot_ens')
            
    datelabel = '%s/%s/%s' % (date.year, str('%02d' % date.month), str('%02d' % date.day))
    yyyymmdd_datelabel = '%s%s%s' % (date.year, str('%02d' % date.month), str('%02d' % date.day))
    
    
    filequery = fcast_in_dir + '/%s/*' % (datelabel)
    
    files_members = glob.glob(filequery)
    files_members.sort()
    
    mems = [memb[-3:] for memb in files_members]
    #mems = ['033', '034', '035']
    print mems
    
    # find the number of lat lon points
    filequery = files_members[0] + '/*.pp'
    print filequery
    data_files = glob.glob(filequery)
    data_files = data_files[0]
    
    #olr = iris.load_cube(data_files, 'toa_outgoing_longwave_flux')
    prec = iris.load_cube(data_files, 'precipitation_flux')
    # subset forecast data and append to analysis
    prec = prec.intersection(latitude=(-11, 21), longitude=(89, 131))
    nlat, nlon = prec.shape
    ntime = 8
    prec_big_cube_data = np.zeros((len(mems), ntime, nlat, nlon))
    
    u850 = iris.load_cube(data_files, 'x_wind')
    u850 = u850.extract(iris.Constraint(pressure=850))
    u850 = u850.intersection(latitude=(-11, 21), longitude=(89, 131))
    print u850, prec
    nlat, nlon = u850.shape
    u850_big_cube_data = np.zeros((len(mems), ntime, nlat, nlon))
    v850_big_cube_data = np.zeros((len(mems), ntime, nlat, nlon))
    speed_big_cube_data = np.zeros((len(mems), ntime, nlat, nlon))
    
    # cold surge metrics
    cs_metric = np.zeros((len(mems), ntime))
    ces_metric = np.zeros((len(mems), ntime))
    
    for n, ens in enumerate(mems):
        filequery = files_members[n] + '/*.pp'
        data_files = glob.glob(filequery)
        data_files.sort()
        
        if not data_files:
            print 'ERROR IN _prepare_forecast_data!!!'
            print '%s files not found in %s for %s' % (infolabel, fcast_in_dir, date)
            sys.exit()
        print data_files
        
        xcubes = iris.load_cube(data_files, 'precipitation_flux')
        prec = xcubes.copy()
        prec.data *= 3600.
        #prec.convert_units('kg m-2 day-1')
        ntime, nlat, nlon = prec.shape
        print np.min(prec.data), np.max(prec.data)
        #prec.data[0] = xcubes.data[0] / 3.
        #for i in range(1, ntime):
        #    #olr[i].data = (olr[i].data - xcubes.data[i - 1]) / 24.
        #    prec.data[i] = (xcubes.data[i] - xcubes.data[i - 1]) / 24.
        #    #cubes.data[i] = (xcubes.data[i] - xcubes.data[i - 1]) / 24.
        #    #print np.min(olr[i].data), np.max(olr[i].data)
            
        u850 = iris.load_cube(data_files, 'x_wind')
        u850 = u850.extract(iris.Constraint(pressure=850))
        
        v850 = iris.load_cube(data_files, 'y_wind')
        v850 = v850.extract(iris.Constraint(pressure=850))
        
        # subset forecast data
        prec = prec.intersection(latitude=(-11, 21), longitude=(89, 131))
        u850 = u850.intersection(latitude=(-11, 21), longitude=(89, 131))
        v850 = v850.intersection(latitude=(-11, 21), longitude=(89, 131))
        #print u850_cubes
        
        speed = u850.copy()
        speed.data = np.sqrt(u850.data ** 2 + v850.data ** 2)
        
        for i in range(ntime):
            # box averages
            u850_ba = u850[i].intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            u850_ba = u850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            v850_ba = v850[i].intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            v850_ba = v850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            speed_ba = speed[i].intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
            speed_ba = speed_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
            
            #print u850_ba.data, v850_ba.data, speed_ba.data
            
            xlon = u850.coord('longitude').points
            ylat = u850.coord('latitude').points
            
            print datelabel, ens, i
            # Check for cross-equatorial surges
            # CP index
            if speed_ba.data >= Chang_threshold and u850_ba.data < 0 and v850_ba.data < 0:
                #print 'Cold surge detected!!!'
                cs_metric[n, i] = 1
                
                # Hattori index
                v850_hattori = v850[i].intersection(latitude=(hattori_box[2], hattori_box[3]), longitude=(hattori_box[0], hattori_box[1]))
                v850_hattori = v850_hattori.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)
                if v850_hattori.data <= Hattori_threshold:
                    #print 'Cross-Equatorial Cold surge detected!!!'
                    ces_metric[n, i] = 1
                                    
        # for ensemble means
        prec_big_cube_data[n] = prec.data
        u850_big_cube_data[n] = u850.data
        v850_big_cube_data[n] = v850.data
        speed_big_cube_data[n] = speed.data
        
        print prec.data.shape
    #print np.mean(olr_big_cube_data, axis=0).shape
    ens_mean_prec = prec.copy()
    ens_mean_prec.data = np.mean(prec_big_cube_data, axis=0)
    
    ens_mean_u850 = u850.copy()
    ens_mean_u850.data = np.mean(u850_big_cube_data, axis=0)
    
    ens_mean_v850 = v850.copy()
    ens_mean_v850.data = np.mean(v850_big_cube_data, axis=0)
    
    ens_mean_speed = speed.copy()
    ens_mean_speed.data = np.mean(speed_big_cube_data, axis=0)
    #fig, axes = plt.subplots(2, 2, figsize=(10,5))
    
    #print cs_metric, ces_metric
    psfiles = []
    for i in range(ntime - 1):
        
        valid_date = date + datetime.timedelta(days=i)
        valid_datelabel = '%s/%s/%s' % (valid_date.year, str('%02d' % valid_date.month), str('%02d' % valid_date.day))
        
        # CS probability
        cs_freq = 100.*np.count_nonzero(cs_metric[:, i] == 1) / len(mems)
        ces_freq = 100.*np.count_nonzero(ces_metric[:, i] == 1) / len(mems)
        
        print i, cs_freq, ces_freq
        
        fig = plt.figure(figsize=(10, 10), dpi=100)
        
        prec = ens_mean_prec[i]
        u850 = ens_mean_u850[i]
        v850 = ens_mean_v850[i]
        speed = ens_mean_speed[i]
        
        lw = 3 * speed.data / 20.0 #speed.data.max()
        
        #cf = iplt.contourf(prec, levels=range(40, 240, 20), cmap='gray', alpha=0.75)
        clevels = [1, 1.2, 1.4, 1.6, 1.8, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, ]
        cf = iplt.contourf(prec, levels=clevels, cmap='gray_r', alpha=0.75)
        #cf = iplt.contourf(prec, levels=range(40, 240, 20))
        axc = plt.gca()
        axc.coastlines('50m')
        axc.set_ylim([-10, 20])
        axc.set_xlim([90, 130])
        axc.stock_img()
        axc.set_yticks([-10, 0, 10, 20], crs=ccrs.PlateCarree())
        axc.set_xticks([90, 100, 110, 120, 130], crs=ccrs.PlateCarree())
        axc.gridlines()
        
        plt.title('Ensemble mean PREC, 850hPa winds \n Forecast start: %s, Lead: T+%s h \n Valid at %s' % (datelabel, (i * 24), valid_datelabel))
        cl = plt.gca().streamplot(xlon, ylat, u850.data, v850.data, density=(2., 2.), color=speed.data, linewidth=lw)
        
        colorbar_axes = plt.gcf().add_axes([0.2, 0.15, 0.6, 0.025])
        colorbar = plt.colorbar(cf, colorbar_axes, orientation='horizontal')

        colorbar_axes = plt.gcf().add_axes([0.92, 0.25, 0.025, 0.5])
        colorbar = plt.colorbar(cl.lines, colorbar_axes, orientation='vertical')
        
        font = {'color':  'darkorange', 'weight': 'bold', 'size': 12}
        axc.text(91, 19, 'COLD SURGE PROB. = %.2f ' % cs_freq, fontdict=font)
            
        font = {'color':  'red', 'weight': 'bold', 'size': 12}
        axc.text(107, 19., 'CROSS-EQUATORIAL SURGE PROB. = %.2f ' % ces_freq, fontdict=font)

        psfile = os.path.join(plot_ens_dir, 'Cold_surge_monitor', 'Cold_surge_monitor_%s_T%sh.ps' % (yyyymmdd_datelabel, (i * 24)))
        psfiles.append(psfile)
        plt.savefig(psfile)
        #plt.show()
    return psfiles        

if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    date = yesterday
    
    datelabel = '%s%s%s' % (date.year, str('%02d' % date.month), \
                                       str('%02d' % date.day))
    # Test
    #plot_hovmoller(datelabel, varlist, label='None', infolabel='None', debug=True)
