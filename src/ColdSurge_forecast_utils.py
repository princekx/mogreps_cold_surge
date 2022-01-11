import os, sys
import glob
import iris
import matplotlib

# use the Agg environment to generate an image rather than outputting to screen
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import iris.plot as iplt
import cartopy.crs as ccrs
import datetime
import numpy as np
import data_paths
from src import retrieve_mogreps_data as mog_retrieve


def cold_surge_probabilities(u850_cube, v850_cube, speed_cube):
    # Cold surge identification
    chang_box = [107, 115, 5, 10]  # CP Chang's 2nd domain

    # Hattori box for cross equatorial surges
    hattori_box = [105, 115, -5, 5]

    Chang_threshold = 9.0  # 10 # wind speed m/s
    Hattori_threshold = -2.0  # m/s meridional wind

    u850_ba = u850_cube.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
    u850_ba = u850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)

    v850_ba = v850_cube.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
    v850_ba = v850_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)

    speed_ba = speed_cube.intersection(latitude=(chang_box[2], chang_box[3]), longitude=(chang_box[0], chang_box[1]))
    speed_ba = speed_ba.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)

    # Hattori index
    v850_hattori = v850_cube.intersection(latitude=(hattori_box[2], hattori_box[3]),
                                          longitude=(hattori_box[0], hattori_box[1]))
    v850_hattori = v850_hattori.collapsed(('latitude', 'longitude'), iris.analysis.MEAN)

    # extract the forecast periods and members from the data
    # to create a metrics array
    forecast_periods = u850_cube.coord('forecast_period').points
    members = u850_cube.coord('realization').points

    # Check for cross-equatorial surges
    # CP index
    mask1 = u850_ba.data > 0.
    mask2 = v850_ba.data > 0.
    mask3 = speed_ba.data <= Chang_threshold
    mask4 = v850_ba.data > Hattori_threshold

    speed_ma = speed_ba.data.copy()
    speed_ma = np.ma.array(speed_ma, mask=mask1)
    speed_ma = np.ma.array(speed_ma, mask=mask2)
    cs_metric = np.ma.array(speed_ma, mask=mask3)

    # CES Hattori index
    ces_metric = np.ma.array(v850_ba.data, mask=mask4)
    ces_metric = np.ma.array(ces_metric, mask=cs_metric.mask)

    # return the probabilities as fraction
    return cs_metric.count(axis=1) / float(len(members)), ces_metric.count(axis=1) / float(len(members))


def plot_forecast_ensemble_mean(forecast_date_time):
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)

    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year, str_month, str_day, str_hour)
    plot_ens_dir = data_paths.dirs('plot_ens')

    # Read the processed and combined data
    precip_file_name = os.path.join(out_data_dir, 'MOG_PRECIP_24H_%s.nc' % (date_label))
    precip_cube = iris.load_cube(precip_file_name)

    u850_file_name = os.path.join(out_data_dir, 'MOG_x_wind_850_24H_%s.nc' % (date_label))
    u850_cube = iris.load_cube(u850_file_name)

    v850_file_name = os.path.join(out_data_dir, 'MOG_y_wind_850_24H_%s.nc' % (date_label))
    v850_cube = iris.load_cube(v850_file_name)

    # Compute speed
    speed_cube = (u850_cube ** 2 + v850_cube ** 2) ** 0.5

    # Compute cold surge probabilities
    cs_prob, ces_prob = cold_surge_probabilities(u850_cube, v850_cube, speed_cube)

    # Ensemble mean
    precip_ens_mean = precip_cube.collapsed('realization', iris.analysis.MEAN)
    u850_ens_mean = u850_cube.collapsed('realization', iris.analysis.MEAN)
    v850_ens_mean = v850_cube.collapsed('realization', iris.analysis.MEAN)
    speed_ens_mean = speed_cube.collapsed('realization', iris.analysis.MEAN)

    xlon = u850_cube.coord('longitude').points
    ylat = u850_cube.coord('latitude').points
    X, Y = np.meshgrid(xlon, ylat)

    ntimes = len(precip_cube.coord('forecast_period').points)

    # Bounds for streamplot
    bounds = np.arange(2, 22, 2)
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=256)

    for t in np.arange(ntimes):
        valid_date = forecast_date_time + datetime.timedelta(days=int(t))
        valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                             str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

        lw = speed_ens_mean[t].data / 7.0  # an adhoc scaling for plotting

        fig = plt.figure(figsize=(9, 8), dpi=100)
        # contour plot of precip
        clevels = [1, 5, 10, 15, 20, 25, 30, 35, 40]
        cf = iplt.contourf(precip_ens_mean[t], levels=clevels, cmap='gray_r', alpha=0.65, extend='max')
        axc = plt.gca()
        axc.coastlines('50m', alpha=0.5)
        axc.set_ylim([-10, 20])
        axc.set_xlim([90, 130])
        axc.stock_img()
        axc.set_yticks([-10, 0, 10, 20], crs=ccrs.PlateCarree())
        axc.set_xticks([90, 100, 110, 120, 130], crs=ccrs.PlateCarree())
        # axc.gridlines()

        plt.title('Ensemble mean PREC, 850hPa winds \n Forecast start: %s, Lead: T+%s h \n Valid for 24H up to %s' % (
            date_label, (t * 24), valid_date_label))

        # overplot wind as streamlines
        cl = plt.gca().streamplot(X, Y, u850_ens_mean[t].data, v850_ens_mean[t].data,
                                  density=(2., 1.5), maxlength=1, norm=norm, cmap='GnBu',
                                  color=speed_ens_mean[t].data, linewidth=lw)

        colorbar_axes = plt.gcf().add_axes([0.2, 0.07, 0.6, 0.025])
        colorbar = plt.colorbar(cf, colorbar_axes, orientation='horizontal', label='Precip (mm day$^{-1}$)')

        colorbar_axes = plt.gcf().add_axes([0.92, 0.25, 0.025, 0.5])
        colorbar = plt.colorbar(cl.lines, colorbar_axes, orientation='vertical', label='Wind Speed (m s$^{-1}$)')

        # Cold surge probabilities markers
        # these are matplotlib.patch.Patch properties
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

        font = {'color': 'red', 'weight': 'bold', 'size': 12}
        axc.text(91, 19, "COLD SURGE: {:.1f}%".format(cs_prob[t] * 100.), fontdict=font, verticalalignment='top',
                 bbox=props, alpha=0.7)

        font = {'color': 'red', 'weight': 'bold', 'size': 12}
        axc.text(91, 17.5, "CROSS-EQUATORIAL SURGE: {:.1f}%".format(ces_prob[t] * 100.), fontdict=font,
                 verticalalignment='top', bbox=props, alpha=0.7)

        png_file = os.path.join(plot_ens_dir,
                                'Cold_surge_EnsMean_%s_T%sh.png' % (date_label, (t * 24)))

        plt.savefig(png_file)
        plt.close()
        fig.clear()
        print('Plotted %s' % png_file)


def plot_forecast_probability(forecast_date_time, precip_thresholds=[10, 20],
                              speed_thresholds=[10, 15]):
    '''
    Plots the probability maps of precip and winds for given thresholds
    :param forecast_date_time:
    :type forecast_date_time:
    :param precip_threshold:
    :type precip_threshold:
    :param speed_threshold:
    :type speed_threshold:
    :return:
    :rtype:
    '''
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)

    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year, str_month, str_day, str_hour)
    plot_ens_dir = data_paths.dirs('plot_ens')

    # Read the processed and combined data
    precip_file_name = os.path.join(out_data_dir, 'MOG_PRECIP_24H_%s.nc' % (date_label))
    precip_cube = iris.load_cube(precip_file_name)

    u850_file_name = os.path.join(out_data_dir, 'MOG_x_wind_850_24H_%s.nc' % (date_label))
    u850_cube = iris.load_cube(u850_file_name)

    v850_file_name = os.path.join(out_data_dir, 'MOG_y_wind_850_24H_%s.nc' % (date_label))
    v850_cube = iris.load_cube(v850_file_name)

    # Compute speed
    speed_cube = (u850_cube ** 2 + v850_cube ** 2) ** 0.5

    for precip_threshold in precip_thresholds:
        for speed_threshold in speed_thresholds:
            # Compute cold surge probabilities
            cs_prob, ces_prob = cold_surge_probabilities(u850_cube, v850_cube, speed_cube)

            precip_prob = precip_cube.collapsed('realization', iris.analysis.PROPORTION,
                                                function=lambda values: values > precip_threshold)
            print(precip_prob)
            speed_prob = speed_cube.collapsed('realization', iris.analysis.PROPORTION,
                                              function=lambda values: values > speed_threshold)

            ntimes = len(precip_cube.coord('forecast_period').points)

            for t in np.arange(ntimes):
                valid_date = forecast_date_time + datetime.timedelta(days=int(t))
                valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                                     str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

                fig = plt.figure(figsize=(9, 8), dpi=100)
                # contour plot of precip
                try:
                    # contour plot of precip
                    clevels = np.arange(0.1, 1.1, 0.1)
                    cf = iplt.contourf(precip_prob[t], levels=clevels, cmap='gray_r', alpha=0.65, extend='max')
                    axc = plt.gca()
                except:
                    axc = plt.subplot(111, projection=ccrs.PlateCarree())

                axc.coastlines('50m', alpha=0.5)
                axc.set_ylim([-10, 20])
                axc.set_xlim([90, 130])
                axc.stock_img()
                axc.set_yticks([-10, 0, 10, 20], crs=ccrs.PlateCarree())
                axc.set_xticks([90, 100, 110, 120, 130], crs=ccrs.PlateCarree())

                clevels = np.arange(0.5, 1.01, 0.1)
                cfc = iplt.contour(speed_prob[t], levels=clevels, linewidths=clevels * 3, extend='max', alpha=0.7)
                # plt.gca().coastlines()

                title = 'Ensemble probability PREC, 850hPa winds \n Forecast start: %s, Lead: T+%s h \n Valid for 24H up to %s' % (
                    date_label, (t * 24), valid_date_label)
                # title += '\n Precip. prob (p$\geq$ %s mm day$^{-1}$)' %precip_threshold
                # title += '\n Wind speed. prob (p$\geq$ %s m s$^{-1}$)' %speed_threshold

                plt.title(title)
                try:
                    colorbar_axes = plt.gcf().add_axes([0.2, 0.07, 0.6, 0.025])
                    cb1 = plt.colorbar(cf, colorbar_axes, orientation='horizontal',
                                       label='Precip. prob (p$\geq$ %s mm day$^{-1}$)' % precip_threshold)

                    colorbar_axes = plt.gcf().add_axes([0.91, 0.25, 0.025, 0.2])
                    cb2 = plt.colorbar(cfc, colorbar_axes, orientation='vertical',
                                       label='Wind speed. prob (V$\geq$ %s m s$^{-1}$)' % speed_threshold)
                    cb2.outline.set_edgecolor('white')
                    # set colorbar ticklabels
                    cb2.ax.tick_params(color="white")
                except:
                    pass

                # Cold surge probabilities markers
                # these are matplotlib.patch.Patch properties
                props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

                font = {'color': 'red', 'weight': 'bold', 'size': 12}
                axc.text(91, 19, "COLD SURGE: {:.1f}%".format(cs_prob[t] * 100.), fontdict=font,
                         verticalalignment='top',
                         bbox=props, alpha=0.7)

                font = {'color': 'red', 'weight': 'bold', 'size': 12}
                axc.text(91, 17.5, "CROSS-EQUATORIAL SURGE: {:.1f}%".format(ces_prob[t] * 100.), fontdict=font,
                         verticalalignment='top', bbox=props, alpha=0.7)

                png_file = os.path.join(plot_ens_dir,
                                        'Cold_surge_ProbMaps_%s_T%sh_Pr%s_Sp%s.png' % (date_label, (t * 24),
                                                                                       precip_threshold,
                                                                                       speed_threshold))

                plt.savefig(png_file)
                plt.close()
                fig.clear()
                print('Plotted %s' % png_file)


if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    date = yesterday

    datelabel = '%s%s%s' % (date.year, str('%02d' % date.month), \
                            str('%02d' % date.day))
    # Test
    # plot_hovmoller(datelabel, varlist, label='None', infolabel='None', debug=True)
