import os, sys
import glob
import iris
import datetime
import numpy as np
from bokeh.plotting import figure, show, save, output_file
from bokeh.models import ColumnDataSource, Patches, Plot, Title
from bokeh.models import  Range1d, LinearColorMapper, ColorBar
from bokeh.models import GeoJSONDataSource
from bokeh.palettes import GnBu9, Magma6, Greys256, Greys9, GnBu9, RdPu9
import data_paths
from src import retrieve_mogreps_data as mog_retrieve
from bokeh_vector import vector

def plot_image_map(plot, cube, **kwargs):
    palette = kwargs['palette']
    if kwargs['cbar_title']:
        cbar_title = kwargs['cbar_title']
    if kwargs['palette_reverse']:
        palette.reverse()
    lons = cube.coord('longitude').points
    lats = cube.coord('latitude').points

    color_mapper = LinearColorMapper(palette=palette, low=kwargs['low'], high=kwargs['high'])
    with open('./bokeh_display/data/custom.geo.json', 'r', encoding="utf-8") as f:
        countries = GeoJSONDataSource(geojson=f.read())

    plot.patches("xs", "ys", color=None, line_color="grey", fill_color='grey', fill_alpha=0.3, source=countries,
                 alpha=0.5)

    plot.image(image=[cube.data], x=min(lons), y=min(lats), dw=max(lons) - min(lons),
               dh=max(lats) - min(lats), color_mapper=color_mapper, alpha=0.7)

    plot.x_range = Range1d(start=min(lons), end=max(lons))
    plot.y_range = Range1d(start=min(lats), end=max(lats))

    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12,
                         border_line_color=None, location=(0, 0),
                         orientation='horizontal', title=cbar_title)
    plot.add_layout(color_bar, 'below')
    return plot


def plot_vectors(plot, u, v, **kwargs):
    xSkip = kwargs.get("xSkip", 4)
    ySkip = kwargs.get("ySkip", 4)
    maxSpeed = kwargs.get("maxSpeed", 10.)
    arrowHeadAngle = kwargs.get("arrowHeadAngle", 25.)
    arrowHeadScale = kwargs.get("arrowHeadScale", 0.2)
    arrowType = kwargs.get("arrowType", "barbed")
    palette = kwargs.get('palette', None)
    palette_reverse = kwargs.get('palette_reverse', False)

    vec = vector(u, v, xSkip=xSkip, ySkip=ySkip,
                 maxSpeed=maxSpeed, arrowType=arrowType, arrowHeadScale=arrowHeadScale,
                 palette=palette, palette_reverse=palette_reverse)

    arrow_source = ColumnDataSource(dict(xs=vec.xs, ys=vec.ys, colors=vec.colors))

    plot.patches(xs="xs", ys="ys", fill_color="colors", line_color="colors", fill_alpha=0.5, source=arrow_source)
    return plot

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

def bokeh_plot_forecast_ensemble_mean(forecast_date_time, plot_width=750):
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

    cube = precip_ens_mean[0]
    lons = cube.coord('longitude').points
    lats = cube.coord('latitude').points

    ntimes = len(precip_cube.coord('forecast_period').points)

    # Plot setup
    width = plot_width
    aspect = (max(lons) - min(lons)) / (max(lats) - min(lats))
    height = int(width / (0.85 * aspect))

    for t in np.arange(ntimes):
        valid_date = forecast_date_time + datetime.timedelta(days=int(t))
        valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                             str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

        title = 'Ensemble mean PREC, 850hPa winds'
        subtitle = 'Forecast start: %s, Lead: T+%s h Valid for 24H up to %s' % (date_label, (t * 24),
                                                                                valid_date_label)

        plot = figure(plot_height=height, plot_width=width, title=None,
                      tools=["pan, reset, save, box_zoom, wheel_zoom, hover"],
                      x_axis_label='Longitude', y_axis_label='Latitude')
        cmap = GnBu9.copy()
        options = {'palette': cmap, 'palette_reverse': True, 'low': 10, 'high': 40}
        plot = plot_image_map(plot, precip_ens_mean[t], **options)

        cmap = RdPu9.copy()
        vector_options = {'palette': cmap, 'palette_reverse': True, 'maxSpeed': 5, 'arrowHeadScale': 0.2,
                          'arrowType': 'barbed'}
        plot = plot_vectors(plot, u850_ens_mean[t], v850_ens_mean[t], **vector_options)

        plot.add_layout(Title(text=subtitle, text_font_style="italic"), 'above')
        plot.add_layout(Title(text=title, text_font_size="16pt"), 'above')

        #show(plot)
        html_file = os.path.join(plot_ens_dir,
                                'Bokeh_Cold_surge_EnsMean_%s_T%sh.html' % (date_label, (t * 24)))
        output_file(html_file)
        save(plot)
        print('Plotted %s' % html_file)

def bokeh_plot_forecast_probability_precip(forecast_date_time, precip_thresholds=[10, 20],
                              speed_thresholds=[10, 15], plot_width=750):
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

    cs_prob, ces_prob = cold_surge_probabilities(u850_cube, v850_cube, speed_cube)

    lons = precip_cube.coord('longitude').points
    lats = precip_cube.coord('latitude').points

    # Plot setup
    width = plot_width
    aspect = (max(lons) - min(lons)) / (max(lats) - min(lats))
    height = int(width / (0.85 * aspect))

    for precip_threshold in precip_thresholds:
        # Compute cold surge probabilities
        precip_prob = precip_cube.collapsed('realization', iris.analysis.PROPORTION,
                                            function=lambda values: values > precip_threshold)

        ntimes = len(precip_cube.coord('forecast_period').points)

        for t in np.arange(ntimes):
            valid_date = forecast_date_time + datetime.timedelta(days=int(t))
            valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                                 str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

            title = 'Ensemble probability of Precipitation'
            subtitle = 'Forecast start: %s, Lead: T+%sh Valid for 24H up to %s' % (date_label, (t * 24),
                                                                                   valid_date_label)
            plot = figure(plot_height=height, plot_width=width, title=None,
                          tools=["pan, reset, save, box_zoom, wheel_zoom, hover"],
                          x_axis_label='Longitude', y_axis_label='Latitude')

            cmap = GnBu9.copy()
            cbar_title = 'Precipitation probability (p >= %s mm/day)' % precip_threshold
            options = {'palette': cmap, 'palette_reverse': True, 'low': 0.1, 'high': 1, 'cbar_title':cbar_title}
            plot = plot_image_map(plot, precip_prob[t], **options)

            plot.add_layout(Title(text=subtitle, text_font_style="italic"), 'above')
            plot.add_layout(Title(text=title, text_font_size="16pt"), 'above')


            html_file = os.path.join(plot_ens_dir, 'Bokeh_Cold_surge_ProbMaps_%s_T%sh_Pr%s.html' % (date_label, (t * 24),
                                                                                   precip_threshold))

            output_file(html_file)
            save(plot)
            print('Plotted %s' % html_file)

def bokeh_plot_forecast_probability_speed(forecast_date_time, speed_thresholds=[10, 15], plot_width=750):
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
    u850_file_name = os.path.join(out_data_dir, 'MOG_x_wind_850_24H_%s.nc' % (date_label))
    u850_cube = iris.load_cube(u850_file_name)

    v850_file_name = os.path.join(out_data_dir, 'MOG_y_wind_850_24H_%s.nc' % (date_label))
    v850_cube = iris.load_cube(v850_file_name)

    # Compute speed
    speed_cube = (u850_cube ** 2 + v850_cube ** 2) ** 0.5

    cs_prob, ces_prob = cold_surge_probabilities(u850_cube, v850_cube, speed_cube)

    lons = v850_cube.coord('longitude').points
    lats = v850_cube.coord('latitude').points

    # Plot setup
    width = plot_width
    aspect = (max(lons) - min(lons)) / (max(lats) - min(lats))
    height = int(width / (0.85*aspect))

    for speed_threshold in speed_thresholds:
        # Compute cold surge probabilities
        speed_prob = speed_cube.collapsed('realization', iris.analysis.PROPORTION,
                                          function=lambda values: values > speed_threshold)

        ntimes = len(speed_prob.coord('forecast_period').points)

        for t in np.arange(ntimes):
            valid_date = forecast_date_time + datetime.timedelta(days=int(t))
            valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                                 str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

            title = 'Ensemble probability of 850hPa wind speed'
            subtitle = 'Forecast start: %s, Lead: T+%sh Valid for 24H up to %s' % (date_label, (t * 24), valid_date_label)
            plot = figure(plot_height=height, plot_width=width, title=None,
                          tools=["pan, reset, save, box_zoom, wheel_zoom, hover"],
                          x_axis_label='Longitude', y_axis_label='Latitude')

            cmap = GnBu9.copy()
            cbar_title = 'Wind speed probability (V>= %s m/s)' % speed_threshold
            options = {'palette': cmap, 'palette_reverse': True, 'low': 0.1, 'high': 1, 'cbar_title':cbar_title}
            plot = plot_image_map(plot, speed_prob[t], **options)

            plot.add_layout(Title(text=subtitle, text_font_style="italic"), 'above')
            plot.add_layout(Title(text=title, text_font_size="16pt"), 'above')

            html_file = os.path.join(plot_ens_dir, 'Bokeh_Cold_surge_ProbMaps_%s_T%sh_Sp%s.html' % (date_label, (t * 24),
                                                                                   speed_threshold))

            output_file(html_file)
            save(plot)
            print('Plotted %s' % html_file)

if __name__ == '__main__':
    today = datetime.date.today()
    #yesterday = today - datetime.timedelta(days=1)
    yesterday = datetime.datetime(2021, 9, 30, 12)

    #bokeh_plot_forecast_ensemble_mean(yesterday)
    bokeh_plot_forecast_probability_precip(yesterday, precip_thresholds=[10])
    #bokeh_plot_forecast_probability_speed(yesterday, speed_thresholds=[5])