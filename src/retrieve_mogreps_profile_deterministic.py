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


def retrieve_mogreps_determin_profile(forecast_date_time):
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
        mem = 0
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
        query_file = os.path.join(query_files_dir, 'mogg_query_profiles')
        local_query_file1 = os.path.join(query_files_dir, 'local_query1_profiles')

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
            outfile = 'englaa_profiles_pd%s.pp' % fc_3d
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

if __name__ == '__main__':
    today = datetime.date.today()
    #yesterday = today - datetime.timedelta(days=1)
    yesterday = datetime.datetime(2021, 9, 20, 12)

    # Do the analysis yesterday
    retrieve_mogreps_determin_profile(yesterday)
