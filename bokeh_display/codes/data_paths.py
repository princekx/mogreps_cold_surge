def dirs(key):
    self = {}
    self['queryfiles'] = '/net/home/h03/hadpx/MJO/Monitoring/mogreps/queryfiles'
    self['mog_moose_dir'] = 'moose:/opfc/atm/mogreps-g/prods/'
    self['mog_forecast_data_dir'] = '/project/MJO_GCSS/MJO_monitoring/raw_data/mogreps'
    self['mog_forecast_out_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/mogreps'
    self['mog_forecast_ascii_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/mogreps/mjo_data_ascii'
    self['analy_out_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/analysis'
    self['analy_in_dir'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/analysis'
    self['plot_ens'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/mogreps/plot_ens'
    self['plot_ens_html'] = '/project/MJO_GCSS/MJO_monitoring/processed_MJO_data/mogreps/plot_ens/html'
    return self[key]
