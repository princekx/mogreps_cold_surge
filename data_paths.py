def dirs(key):
    self = {}
    self['queryfiles'] = '/net/home/h03/hadpx/MJO/Monitoring/mogreps_cold_surge/queryfiles'
    self['mog_moose_dir'] = 'moose:/opfc/atm/mogreps-g/prods/'
    self['mog_forecast_data_dir'] = '/scratch/hadpx/cold_surge_monitoring/mogreps/raw_data'
    self['mog_forecast_out_dir'] = '/scratch/hadpx/cold_surge_monitoring/mogreps/processed_data'
    # self['mog_forecast_ascii_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/mogreps/mjo_data_ascii'
    # self['analy_out_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/analysis'
    # self['analy_in_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/analysis'
    self['plot_ens'] = '/project/MJO_GCSS/cold_surge_monitoring/mogreps/plot_ens'
    return self[key]
