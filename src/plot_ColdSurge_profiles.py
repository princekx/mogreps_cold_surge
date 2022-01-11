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


def find_nearest_in_list(myList, myNumber):
    return min(myList, key=lambda x: abs(x - myNumber))


def get_cube_coords_along_line(cube, start_coords=None, end_coords=None):
    '''
    Generate a (lat, lon) pair of cube coordinates along a line
    made up of start and end points
    '''
    if not (start_coords is None) or (end_coords is None):
        lons = cube.coord('longitude').points
        lats = cube.coord('latitude').points

        # Find the actual coordinate values between the points
        # Bit of overkill, but want to make sure there are no round off errors
        # when calling the lat/lon values in the extraction step
        # r_lons = [find_nearest_in_list(lons, rlon) for rlon in np.arange(find_nearest_in_list(lons, start_coords[0]),
        #                                                      find_nearest_in_list(lons, end_coords[0]), dlon)]
        # r_lats = [find_nearest_in_list(lats, rlat) for rlat in np.arange(find_nearest_in_list(lats, start_coords[1]),
        #                                                      find_nearest_in_list(lats, end_coords[1]), dlat)]

        # Find the actual coordinate values between the points
        lon1, lat1 = start_coords
        lon2, lat2 = end_coords
        if lon1 < lon2:
            r_lons = lons[(lon1 < lons) & (lons <= lon2)]
        else:
            r_lons = lons[(lon2 < lons) & (lons <= lon1)][::-1]

        if lat1 < lat2:
            r_lats = lats[(lat1 < lats) & (lats <= lat2)]
        else:
            r_lats = lats[(lat2 < lats) & (lats <= lat1)][::-1]

        # print(r_lats)
        # Generate a line from start to end points
        # slope of the line y = mx + b
        # m = slope = (y1-y2)/(x1-x2)
        m = (r_lats[-1] - r_lats[0]) / (r_lons[-1] - r_lons[0])

        # b = y-intercept = (x1*y2 - x2*y1)/(x1-x2)
        b = (r_lons[0] * r_lats[-1] - r_lons[-1] * r_lats[0]) / (r_lons[0] - r_lons[-1])

        # lat points for all lon points along the line
        ys = [m * x + b for x in r_lons]

        # get the corresponding lat values from the coordinate list
        ys_lats = [find_nearest_in_list(lats, yy) for yy in ys]

        return r_lons, ys_lats
    else:
        print('Start/End coordinates missing.')


def cross_section_along_path(cube, lons=None, lats=None):
    cross_section = []
    # Extracting each point and appending
    for ylat, xlon in zip(lats, lons):
        cross_section.append(cube.extract(iris.Constraint(latitude=ylat, longitude=xlon)))

    # merging to a single cube
    # longitude values is given as aux coordinate
    return iris.cube.CubeList(cross_section).merge_cube()


def plot_maps_profiles(forecast_date_time, varname='relative_humidity', member='000',
                       start_coords=(100, 0), end_coords=(120, 20), map_level=700,
                       clevels = np.arange(0, 110, 10)):
    '''
    Plots the maps and vertical profiles alone a line
    :param forecast_date_time:
    :type forecast_date_time:
    :param varname:
    :type varname:
    :param member:
    :type member:
    :param start_coords: tuple(lon, lat)
    :type start_coords: tuple(lon, lat)
    :param end_coords: tuple(lon, lat)
    :type end_coords: tuple(lon, lat)
    :param map_level:
    :type map_level:
    :return:
    :rtype:
    '''
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    plot_ens_dir = data_paths.dirs('plot_ens')
    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'), str_year, str_month, str_day, str_hour,
                                member)

    fc_times_all = np.arange(0, 192, 24)

    for iloc in range(len(fc_times_all)):
        filename = os.path.join(out_data_dir, 'englaa_profiles_pd%s.pp' % str('%03d' % fc_times_all[iloc]))

        valid_date = forecast_date_time + datetime.timedelta(days=iloc)
        valid_date_label = '%s/%s/%s_%sZ' % (valid_date.year, str('%02d' % valid_date.month),
                                             str('%02d' % valid_date.day), str('%02d' % valid_date.hour))

        print(valid_date_label)
        if os.path.exists(filename):
            cube = iris.load_cube(filename, varname)
            cube = cube.intersection(latitude=(-30, 30), longitude=(80, 140))

            # Coordinates alone the line connecting the start and end points
            xlons, ylats = get_cube_coords_along_line(cube, start_coords=start_coords, end_coords=end_coords)

            # get the cube of data along that line
            cross_sect_cube = cross_section_along_path(cube, lons=xlons, lats=ylats)

            # This cube will have lat or lon as the dim coordinate depending on the major axis
            # we need to get this info sorted for plotting.
            if ('latitude' in [cd.standard_name for cd in cross_sect_cube.dim_coords]) and (
                    'longitude' in [cd.standard_name for cd in cross_sect_cube.aux_coords]):
                section_dim_coord = cross_sect_cube.coord('latitude')
                section_aux_coord = cross_sect_cube.coord('longitude')
            elif ('latitude' in [cd.standard_name for cd in cross_sect_cube.aux_coords]) and (
                    'longitude' in [cd.standard_name for cd in cross_sect_cube.dim_coords]):
                section_dim_coord = cross_sect_cube.coord('longitude')
                section_aux_coord = cross_sect_cube.coord('latitude')
            else:
                print('Something wrong with coordinates.')

            pressure_coord_points = cross_sect_cube.coord('pressure').points
            dim_coord_points = section_dim_coord.points
            aux_coord_points = section_aux_coord.points

            P, L = np.meshgrid(pressure_coord_points, dim_coord_points)

            # definitions for the axes
            left, width = 0.05, 0.4
            bottom, height = 0.1, 0.7
            spacing = 0.065

            rect_map = [left, bottom, width, height]

            fig = plt.figure(figsize=(12, 6), dpi=100)

            ax1 = fig.add_axes(rect_map, projection=ccrs.PlateCarree())
            pos1 = ax1.get_position()  # get the original position

            cf = iplt.contourf(cube.extract(iris.Constraint(pressure=map_level)), cmap='RdBu',
                               levels=clevels, extend='both')
            ax1.scatter(xlons, ylats, color='orange', alpha=0.7)
            ax1.plot([start_coords[0], end_coords[0]], [start_coords[1], end_coords[1]], color='red', alpha=0.7)
            ax1.set_title('%s %shPa \n Forecast start: %s, Lead: T+%s h \n '
                                'Valid for 24H up to %s' % (varname, map_level, date_label,
                                                            (iloc * 24),
                                                            valid_date_label), fontsize=10)
            ax1 = plt.gca()
            ax1.coastlines('50m', alpha=0.5)
            ax1.stock_img()
            ax1.set_ylim([-10, 25])
            ax1.set_xlim([90, 130])
            #ax1.grid(alpha=0.5)
            gl = ax1.gridlines(draw_labels=True, alpha=0.5)
            gl.xlabels_top = False
            gl.ylabels_right = False

            pos2 = [pos1.x0 + pos1.width + spacing, pos1.y0, pos1.width + spacing, pos1.height]
            ax2 = fig.add_axes(pos2)

            CS = plt.contourf(L, P, cross_sect_cube.data, cmap='RdBu', levels=clevels, extend='both')
            plt.colorbar(CS, orientation='horizontal')

            xlocs = ax2.get_xticks()
            ylocs = np.interp(xlocs, dim_coord_points, aux_coord_points)

            x_labels = ['%.0f\n%.0f' % (np.floor(xx), np.floor(yy)) for xx, yy in zip(xlocs, ylocs)]
            ax2.set_xticks(xlocs)
            ax2.set_xticklabels(x_labels)
            ax2.tick_params(axis="x", labelsize=8)
            ax2.tick_params(axis="y", labelsize=8)
            ax2.invert_yaxis()
            ax2.grid(alpha=0.5)

            ax2.set_title('%s Cross-section along the line \n Forecast start: %s, Lead: T+%s h \n '
                      'Valid for 24H up to %s' % (varname,
                                                  date_label,
                                                  (iloc * 24),
                                                  valid_date_label), fontsize=10)

            png_file = os.path.join(plot_ens_dir,
                                    'Cold_surge_map_profiles_%s_%s_T%sh.png' % (varname, date_label, (iloc * 24)))

            plt.savefig(png_file)
            plt.close()
            fig.clear()
            print('Plotted %s' % png_file)


if __name__ == '__main__':
    yesterday = datetime.datetime(2021, 9, 20, 12)
    #plot_maps_profiles(yesterday, varname='air_temperature', map_level=1000, clevels=np.arange(240, 320, 5))
    plot_maps_profiles(yesterday, varname='y_wind', map_level=850, clevels=np.arange(-10, 10, 2))