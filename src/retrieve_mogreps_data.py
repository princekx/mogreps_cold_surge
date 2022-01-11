import glob
import os
import sys
import datetime
import data_paths
import numpy as np
import iris


def convert_dim2aux(cube, coord_name='time'):
    '''
    Converting an existing Dim coordinate to an Aux coordinate
    to assist with merging cubes with scalar Aux coordinates
    :param cube:
    :type cube:
    :param coord_name:
    :type coord_name:
    :return:
    :rtype:
    '''
    dim_coord = cube.coord(coord_name)
    aux_coord = iris.coords.AuxCoord(dim_coord.points, standard_name=dim_coord.standard_name,
                                     var_name=dim_coord.var_name, bounds=dim_coord.bounds,
                                     units=dim_coord.units)
    if cube.coords(coord_name):
        cube.remove_coord(coord_name)

    cube.add_aux_coord(aux_coord)
    return cube


def subset_seasia(cube):
    return cube.intersection(latitude=(-15, 25), longitude=(85, 135))


def retrieve_mogreps_forecast_data(forecast_date_time):
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    print('Doing date : %s' % date_label)
    query_files_dir = data_paths.dirs('queryfiles')

    print(query_files_dir)
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # !!!!!! BUG ALERT !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Bug in MOGREPS data archival. It only archives 12 members. 
    # Correct this once the full 36 members are available on moose.
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # This is the correct path for prod run
    moosedir = data_paths.dirs('mog_moose_dir') + '%s%s.pp' % (str_year, str_month)

    # Use this for temporary use for PS39 bug
    # moosedir = data_paths.dirs('mog_moose_dir')# + '%s%s.pp' % (str_year, str_month)

    if forecast_date_time.hour == 12:
        hr_list = [12, 18]
    elif forecast_date_time.hour == 0:
        hr_list = [0, 6]

    fc_times = np.arange(0, 174, 24)
    print(fc_times)

    # Loop over hour

    for hr in hr_list:
        if hr in [0, 12]:
            all_members = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        if hr in [6, 18]:
            all_members = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 0]
        for mem in all_members:
            if (hr in [6, 18]) and mem == 0:
                digit3_mem = '035'
                digit2_mem = '00'
            else:
                digit3_mem = str('%03d' % mem)
                digit2_mem = str('%02d' % mem)

            print('Member is %s' % mem)
            remote_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'),
                                           str_year, str_month, str_day, str_hour, digit3_mem)

            if not os.path.exists(remote_data_dir):
                print('Making dir: %s' % remote_data_dir)
                os.makedirs(remote_data_dir)
                # os.system('ls %s' %remote_data_dir)

            # os.system('moo ls %s' %file_moose)
            query_file = os.path.join(query_files_dir, 'mogg_query')
            local_query_file1 = os.path.join(query_files_dir, 'local_query1')

            # check if the directory is empty

            for fc in fc_times:
                print(fc)
                fcx = fc.copy()
                if fc == 0:
                    fcx = 3

                fct = str('%03d' % fcx)
                fc_3d = str('%03d' % fc)
                print('Forecast is %s ' % fct)
                filemoose = 'prods_op_mogreps-g_%s%s%s_%s_%s_%s.pp' % (str_year,
                                                                       str_month,
                                                                       str_day, str('%02d' % hr),
                                                                       digit2_mem, fct)
                outfile = 'englaa_pd%s.pp' % fc_3d
                file_moose = os.path.join(moosedir, filemoose)
                print(file_moose)

                try:
                    # Replace the fctime and filemoose in query file
                    replacements = {'fctime': fct, 'filemoose': filemoose}

                    with open(query_file) as query_infile, \
                            open(local_query_file1, 'w') as query_outfile:
                        for line in query_infile:
                            for src, target in replacements.items():
                                line = line.replace(src, target)
                            query_outfile.write(line)

                    # do the retrieval
                    remote_data_dir_outfile = '%s/%s' % (remote_data_dir, outfile)

                    if not os.path.exists(remote_data_dir_outfile):
                        command = '/opt/moose-client-wrapper/bin/moo select %s %s %s' % (local_query_file1, \
                                                                                         moosedir, \
                                                                                         remote_data_dir_outfile)
                        print(command)
                        os.system(command)
                    else:
                        print('%s found. Skipping retrieval...' % remote_data_dir_outfile)
                except Exception as e:
                    print(e)
                # print('%s not returned. Check file on moose' %file_moose)
                # sys.exit()
            # else:
            #    print('%s has files. Skipping retrieval...' %remote_data_dir)


def prepare_24hr_precip_accum(forecast_date_time):
    '''
    Retrieved precip data contains 3 x 1 hourly accumulations
    per date. For example for 8 August 2021 00Z
    T+000 contains precip[T-2h, T-1, T0] accumulations
    T+024 contauns precip[T+22, T+23, T+24] accumulations
    Process this to generate 24 hr accumulations for each 24 hr
    :param date:
    :type date:
    :return:
    :rtype:
    '''
    print('Processing precip 24hrs')
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    print('Doing date : %s' % date_label)
    remote_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'),
                                   str_year, str_month, str_day, str_hour)

    # output file
    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year,
                                str_month, str_day, str_hour)
    if not os.path.exists(out_data_dir):
        print('Making dir: %s' % out_data_dir)
        os.makedirs(out_data_dir)

    processed_file_name = os.path.join(out_data_dir, 'MOG_PRECIP_24H_%s.nc' % date_label)
    if not os.path.exists(processed_file_name):
        files_members = glob.glob(os.path.join(remote_data_dir, '*'))
        files_members.sort()
        members = [ff.split('/')[-1] for ff in files_members]
        fc_times_all = np.arange(0, 192, 24)

        precip_24hr_accum = []
        for member in members:
            print('Processing member: %s' % member)
            data_mem_dir = os.path.join(remote_data_dir, member)
            # a new realizaton cordinate
            realiz_coord = iris.coords.AuxCoord([int(member)], standard_name='realization', var_name='realization')
            for iloc, fc_time in enumerate(fc_times_all):
                if iloc == 0:
                    filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                    cube_curr = iris.load_cube(filename_current, 'precipitation_amount')
                    cube_curr = subset_seasia(cube_curr)
                    # print(cube_curr.coord('time'))
                    # 3 hourly sum for the analysis value
                    # Not sure if this is accurate
                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp = cube_curr[-1].copy()
                    else:
                        temp = cube_curr.copy()

                    # removing existing realization coord and adding a
                    # freshly cooked one
                    if temp.coords('realization'):
                        temp.remove_coord('realization')
                    temp.add_aux_coord(realiz_coord)

                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp.data = (cube_curr[-1].data - cube_curr[0].data) * 8.

                    precip_24hr_accum.append(temp)
                else:
                    filename_previous = os.path.join(data_mem_dir,
                                                     'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc - 1]))
                    filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                    # print(filename_current)
                    # print(filename_previous)
                    cube_prev = iris.load_cube(filename_previous, 'precipitation_amount')
                    cube_prev = subset_seasia(cube_prev)
                    cube_curr = iris.load_cube(filename_current, 'precipitation_amount')
                    cube_curr = subset_seasia(cube_curr)

                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp = cube_curr[-1].copy()
                    else:
                        temp = cube_curr.copy()

                    # removing existing realization coord and adding a
                    # freshly cooked one
                    if temp.coords('realization'):
                        temp.remove_coord('realization')
                    temp.add_aux_coord(realiz_coord)

                    # check if the cubes are 3d
                    if len(cube_prev.shape) == 3:
                        temp.data -= cube_prev[-1].data
                    else:
                        temp.data -= cube_prev.data

                    precip_24hr_accum.append(temp)

        # A safety net for merging
        # Converting the scalar dim coordinates to
        # aux coordinate for all cubes
        for cube in precip_24hr_accum:
            convert_dim2aux(cube, coord_name='time')
            convert_dim2aux(cube, coord_name='forecast_period')
            convert_dim2aux(cube, coord_name='forecast_reference_time')
            print(cube.coord('forecast_reference_time'))

        cubes = iris.cube.CubeList(precip_24hr_accum).merge_cube()

        # Time is usually an aux coord because the lower bound is always fixed.
        # Altering this by guessing the bounds so that it will be treated as a
        # Single neat cube rather than many files in the following stages.
        # DO NOT TRUST THE TIME COORDINATE AFTER THIS STEP. THIS IS JUST
        # A MANIPULATION FOR EASE OF COMPUTATIONS.
        if cubes.coord('forecast_period').bounds is not None:
            cubes.coord('forecast_period').bounds = None
            cubes.coord('forecast_period').guess_bounds()

        # Promoting time to a dim coordinate
        iris.util.promote_aux_coord_to_dim_coord(cubes, 'forecast_period')

        # Write data
        iris.save(cubes, processed_file_name)
        print('Processed data written to %s' % processed_file_name)
    else:
        print('Processed data exists in %s. Skipping...' % processed_file_name)

def prepare_24hr_precip_accum_nonIrisWay(forecast_date_time):
    '''
    Iris is a time waster when it comes to merging. Avoid it!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Retrieved precip data contains 3 x 1 hourly accumulations
    per date. For example for 8 August 2021 00Z
    T+000 contains precip[T-2h, T-1, T0] accumulations
    T+024 contauns precip[T+22, T+23, T+24] accumulations
    Process this to generate 24 hr accumulations for each 24 hr
    :param date:
    :type date:
    :return:
    :rtype:
    '''
    print('Processing precip 24hrs')
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    print('Doing date : %s' % date_label)
    remote_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'),
                                   str_year, str_month, str_day, str_hour)

    # output file
    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year,
                                str_month, str_day, str_hour)
    if not os.path.exists(out_data_dir):
        print('Making dir: %s' % out_data_dir)
        os.makedirs(out_data_dir)

    processed_file_name = os.path.join(out_data_dir, 'MOG_PRECIP_24H_%s.nc' % date_label)
    if not os.path.exists(processed_file_name):
        files_members = glob.glob(os.path.join(remote_data_dir, '*'))
        files_members.sort()
        members = [ff.split('/')[-1] for ff in files_members]
        fc_times_all = np.arange(0, 192, 24)

        # read a dummy for generating array
        data_mem_dir = os.path.join(remote_data_dir, '000')
        filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[0]))
        cube_dum = iris.load_cube(filename_current, 'precipitation_amount')
        cube_dum = subset_seasia(cube_dum)
        nlat = len(cube_dum.coord('latitude').points)
        nlon = len(cube_dum.coord('longitude').points)

        # generate a cube to hold data
        precip_24hr_accum = np.ndarray(shape=(len(members), len(fc_times_all) , nlat, nlon), dtype=float)
        realiz_coord = iris.coords.DimCoord([int(mem) for mem in members], standard_name='realization',
                                            var_name='realization')
        forecast_period_coord = iris.coords.DimCoord([int(fct) for fct in fc_times_all],
                                                     standard_name='forecast_period', var_name='forecast_period')
        precip_24hr_accum = iris.cube.Cube(precip_24hr_accum)
        precip_24hr_accum.add_dim_coord(realiz_coord, 0)
        precip_24hr_accum.add_dim_coord(forecast_period_coord, 1)
        precip_24hr_accum.add_dim_coord(cube_dum.coord('latitude'), 2)
        precip_24hr_accum.add_dim_coord(cube_dum.coord('longitude'), 3)
        precip_24hr_accum.add_aux_coord(cube_dum.coord('forecast_reference_time'))
        #precip_24hr_accum.add_aux_coord(cube_dum.coord('time'))

        for member in members:
            print('Processing member: %s' % member)
            data_mem_dir = os.path.join(remote_data_dir, member)
            # a new realizaton cordinate
            for iloc, fc_time in enumerate(fc_times_all):
                if iloc == 0:
                    filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                    cube_curr = iris.load_cube(filename_current, 'precipitation_amount')
                    cube_curr = subset_seasia(cube_curr)
                    # print(cube_curr.coord('time'))
                    # 3 hourly sum for the analysis value
                    # Not sure if this is accurate
                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp = cube_curr[-1].copy()
                    else:
                        temp = cube_curr.copy()

                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp.data = (cube_curr[-1].data - cube_curr[0].data) * 8.

                    precip_24hr_accum.data[int(member), iloc] = temp.data
                else:
                    filename_previous = os.path.join(data_mem_dir,
                                                     'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc - 1]))
                    filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                    # print(filename_current)
                    # print(filename_previous)
                    cube_prev = iris.load_cube(filename_previous, 'precipitation_amount')
                    cube_prev = subset_seasia(cube_prev)
                    cube_curr = iris.load_cube(filename_current, 'precipitation_amount')
                    cube_curr = subset_seasia(cube_curr)

                    # check if the cubes are 3d
                    if len(cube_curr.shape) == 3:
                        temp = cube_curr[-1].copy()
                    else:
                        temp = cube_curr.copy()


                    # check if the cubes are 3d
                    if len(cube_prev.shape) == 3:
                        temp.data -= cube_prev[-1].data
                    else:
                        temp.data -= cube_prev.data

                    precip_24hr_accum.data[int(member), iloc] = temp.data

        print(precip_24hr_accum)
        # Write data
        iris.save(precip_24hr_accum, processed_file_name)
        print('Processed data written to %s' % processed_file_name)
    else:
        print('Processed data exists in %s. Skipping...' % processed_file_name)

def prepare_24hr_wind(forecast_date_time, varname='x_wind', level=850):
    '''
    Process this to extract 24 hr mean winds
    :param date:
    :type date:
    :return:
    :rtype:
    '''
    print('Processing %s %s' % (varname, level))
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    print('Doing date : %s' % date_label)
    remote_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'),
                                   str_year, str_month, str_day, str_hour)

    # output file
    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year,
                                str_month, str_day, str_hour)
    if not os.path.exists(out_data_dir):
        print('Making dir: %s' % out_data_dir)
        os.makedirs(out_data_dir)

    processed_file_name = os.path.join(out_data_dir, 'MOG_%s_%s_24H_%s.nc' %
                                       (varname, level, date_label))

    if not os.path.exists(processed_file_name):
        files_members = glob.glob(os.path.join(remote_data_dir, '*'))
        files_members.sort()
        members = [ff.split('/')[-1] for ff in files_members]
        fc_times_all = np.arange(0, 192, 24)

        # Level constraint for wind data
        level_constraint = iris.Constraint(pressure=level)

        wind_cubes = []
        for member in members:
            print('Processing member: %s' % member)
            data_mem_dir = os.path.join(remote_data_dir, member)
            # a new realizaton cordinate
            realiz_coord = iris.coords.AuxCoord([int(member)], standard_name='realization', var_name='realization')

            for iloc, fc_time in enumerate(fc_times_all):
                filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                cube_curr = iris.load_cube(filename_current, varname)
                cube_curr = cube_curr.extract(level_constraint)
                cube_curr = subset_seasia(cube_curr)

                # print(cube_curr.coord('time'))
                # 3 hourly sum for the analysis value
                # Not sure if this is accurate
                # removing existing realization coord and adding a
                # freshly cooked one
                if cube_curr.coords('realization'):
                    cube_curr.remove_coord('realization')
                cube_curr.add_aux_coord(realiz_coord)

                wind_cubes.append(cube_curr)

        cubes = iris.cube.CubeList(wind_cubes).merge_cube()

        # Time is usually an aux coord because the lower bound is always fixed.
        # Altering this by guessing the bounds so that it will be treated as a
        # Single neat cube rather than many files in the following stages.
        # DO NOT TRUST THE TIME COORDINATE AFTER THIS STEP. THIS IS JUST
        # A MANIPULATION FOR EASE OF COMPUTATIONS.
        if cubes.coord('forecast_period').bounds is not None:
            cubes.coord('forecast_period').bounds = None
            cubes.coord('forecast_period').guess_bounds()

        # Promoting time to a dim coordinate
        iris.util.promote_aux_coord_to_dim_coord(cubes, 'forecast_period')

        # Write data
        iris.save(cubes, processed_file_name)
        print('Processed data written to %s' % processed_file_name)
    else:
        print('Processed data exists in %s. Skipping...' % processed_file_name)

def prepare_24hr_wind_nonIrisWay(forecast_date_time, varname='x_wind', level=850):
    '''
    Process this to extract 24 hr mean winds
    :param date:
    :type date:
    :return:
    :rtype:
    '''
    print('Processing %s %s' % (varname, level))
    str_year, str_month, str_day, str_hour = str(forecast_date_time.year), \
                                             str('%02d' % forecast_date_time.month), \
                                             str('%02d' % forecast_date_time.day), \
                                             str('%02d' % forecast_date_time.hour)

    date_label = '%s%s%s_%sZ' % (str_year, str_month, str_day, str_hour)
    print('Doing date : %s' % date_label)
    remote_data_dir = os.path.join(data_paths.dirs('mog_forecast_data_dir'),
                                   str_year, str_month, str_day, str_hour)

    # output file
    out_data_dir = os.path.join(data_paths.dirs('mog_forecast_out_dir'), str_year,
                                str_month, str_day, str_hour)
    if not os.path.exists(out_data_dir):
        print('Making dir: %s' % out_data_dir)
        os.makedirs(out_data_dir)

    processed_file_name = os.path.join(out_data_dir, 'MOG_%s_%s_24H_%s.nc' %
                                       (varname, level, date_label))

    if not os.path.exists(processed_file_name):
        files_members = glob.glob(os.path.join(remote_data_dir, '*'))
        files_members.sort()
        members = [ff.split('/')[-1] for ff in files_members]
        fc_times_all = np.arange(0, 192, 24)

        # Level constraint for wind data
        level_constraint = iris.Constraint(pressure=level)

        # read a dummy for generating array
        data_mem_dir = os.path.join(remote_data_dir, '000')
        filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[0]))
        cube_dum = iris.load_cube(filename_current, varname)
        cube_dum = cube_dum.extract(level_constraint)
        cube_dum = subset_seasia(cube_dum)
        nlat = len(cube_dum.coord('latitude').points)
        nlon = len(cube_dum.coord('longitude').points)

        # generate a cube to hold data
        wind_cubes = np.ndarray(shape=(len(members), len(fc_times_all), nlat, nlon), dtype=float)
        realiz_coord = iris.coords.DimCoord([int(mem) for mem in members], standard_name='realization',
                                            var_name='realization')
        forecast_period_coord = iris.coords.DimCoord([int(fct) for fct in fc_times_all],
                                                     standard_name='forecast_period', var_name='forecast_period')
        wind_cubes = iris.cube.Cube(wind_cubes)
        wind_cubes.add_dim_coord(realiz_coord, 0)
        wind_cubes.add_dim_coord(forecast_period_coord, 1)
        wind_cubes.add_dim_coord(cube_dum.coord('latitude'), 2)
        wind_cubes.add_dim_coord(cube_dum.coord('longitude'), 3)
        wind_cubes.add_aux_coord(cube_dum.coord('forecast_reference_time'))

        for member in members:
            print('Processing member: %s' % member)
            data_mem_dir = os.path.join(remote_data_dir, member)

            for iloc, fc_time in enumerate(fc_times_all):
                filename_current = os.path.join(data_mem_dir, 'englaa_pd%s.pp' % str('%03d' % fc_times_all[iloc]))
                cube_curr = iris.load_cube(filename_current, varname)
                cube_curr = cube_curr.extract(level_constraint)
                cube_curr = subset_seasia(cube_curr)

                # print(cube_curr.coord('time'))
                # 3 hourly sum for the analysis value
                # Not sure if this is accurate
                # removing existing realization coord and adding a
                # freshly cooked one
                wind_cubes.data[int(member), iloc] = cube_curr.data

        # Write data
        iris.save(wind_cubes, processed_file_name)
        print('Processed data written to %s' % processed_file_name)
    else:
        print('Processed data exists in %s. Skipping...' % processed_file_name)

if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    # yesterday = datetime.date(2016, 4, 24)

    # Do the analysis yesterday
    retrieve_mogreps_forecast_data(yesterday)
