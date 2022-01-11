import datetime
import glob
import os
import sys
import numpy as np
import data_paths


def select_menu_generator(menu_name, menu_label, values, init_value=None):
    # menus = "<select id="+menu_name+"""\" onchange="setPicture();"> \n"""
    # menus = "<p> %s : </p> \n" % menu_label
    menus = """<select id="%s" onchange="setPicture();"> \n""" % menu_name
    menus += """<option class="optionGroup" selected disabled>%s</option> \n""" %menu_label
    for value in values:
        if value == init_value:
            menus += """<option value="%s" selected>%s</option> \n""" % (init_value, init_value)
        else:
            menus += "<option value=\"" + value + "\">" + value + "</option> \n"
    menus += "</select>\n"
    return menus


def get_figure_meta_data(fig_dir):
    dum_files = glob.glob(os.path.join(fig_dir, 'Cold_surge_ProbMaps_*.png'))
    fcast_dates = list(set([(file.split('.')[0].split('_')[-5]) for file in dum_files]))
    fcast_dates.sort(reverse=True)
    fcast_hours = list(set([file.split('.')[0].split('_')[-4] for file in dum_files]))
    fcast_leads = [str(l) for l in np.unique([int(file.split('.')[0].split('_')[-3][1:-1]) for file in dum_files])]
    pr_thresholds = [str(p) for p in list(np.unique([int(file.split('.')[0].split('_')[-2][2:]) for file in dum_files]))]
    sp_thresholds = [str(s) for s in list(np.unique([int(file.split('.')[0].split('_')[-1][2:]) for file in dum_files]))]
    return fcast_dates, fcast_hours, fcast_leads, pr_thresholds, sp_thresholds


def write_html_page_instantaneous(forecast_date, varname='relative_humdity'):
    fig_dir = os.path.join(data_paths.dirs('plot_ens'))
    fcast_dates, fcast_hours, leads, pr_thresholds, sp_thresholds = get_figure_meta_data(fig_dir)

    print(fcast_dates)
    fcast_leads = ['T' + '{0:+}'.format(int(lead)).zfill(4) for lead in leads]

    # Newest dates first
    print(fcast_leads)
    first_url_ensmean = './Cold_surge_EnsMean_%s_%s_T%sh.png' % (fcast_dates[0],
                                                                 fcast_hours[0],
                                                                 leads[0])
    first_url_prob = './Cold_surge_ProbMaps_%s_%s_T%sh_Pr%s_Sp%s.png' % (fcast_dates[0],
                                                                         fcast_hours[0],
                                                                         leads[0],
                                                                         pr_thresholds[0],
                                                                         sp_thresholds[0])
    first_url_prof = './Cold_surge_map_profiles_%s_%s_%s_T%sh.png' % (varname, fcast_dates[0],
                                                                         fcast_hours[0],
                                                                         leads[0])

    print(first_url_ensmean)
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Cold Surge monitor</title>
    <style>
    body {
      background-color: white;
      text-align: center;
      color: black;
      font-family: Arial, Helvetica, sans-serif;
    }
    </style>
    </head>
    <body>
    <h1>Cold Surges monitor</h1>
    """
    html += select_menu_generator("DateMenu", "Forecast date", fcast_dates, init_value=fcast_dates[0])
    html += select_menu_generator("HourMenu", "Forecast hour", fcast_hours, init_value=fcast_hours[0])
    html += select_menu_generator("LeadMenu", "Forecast lead (H)", leads, init_value=leads[0])
    html += select_menu_generator("PrThresholdMenu", "Precip threshold (mm/day)", pr_thresholds,
                                  init_value=pr_thresholds[0])
    html += select_menu_generator("SpThresholdMenu", "Wind speed threshold (m/s)", sp_thresholds,
                                  init_value=sp_thresholds[0])

    html += """
        <div class="row">
            <img id="ensmean_image" style="width:40%" src=\"""" + first_url_ensmean + """\">
            <img id="prob_image" style="width:40%" src=\"""" + first_url_prob + """\" >
            <img id="prof_image" style="width:80%" src=\"""" + first_url_prof + """\" >
        </div>


        <div class="row">
        <button onclick="previousLeadTime()">Previous frame</button>
        <button onclick="nextLeadTime()">Next frame</button>
        """

    html += """
        </div>
        <script>
        function setPicture() {
                var date_value = DateMenu.options[DateMenu.selectedIndex].value;
                var hour_value = HourMenu.options[HourMenu.selectedIndex].value;
                var fcast_lead_value = LeadMenu.options[LeadMenu.selectedIndex].value;
                var pr_threshold_value = PrThresholdMenu.options[PrThresholdMenu.selectedIndex].value;
                var sp_threshold_value = SpThresholdMenu.options[SpThresholdMenu.selectedIndex].value;
                src = \'""" + """./Cold_surge_EnsMean_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h.png';      
                document.getElementById("ensmean_image").src = src;

                src = \'""" + """./Cold_surge_ProbMaps_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h_Pr'+pr_threshold_value+'_Sp'+sp_threshold_value+'.png';      
                document.getElementById("prob_image").src = src;
                
                src = \'""" + """./Cold_surge_map_profiles_relative_humidity_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h.png';      
                document.getElementById("prof_image").src = src;
        }
        </script>
        """

    html += """
            </div>
            <script>
            function previousLeadTime() {
                    var date_value = DateMenu.options[DateMenu.selectedIndex].value;
                    var hour_value = HourMenu.options[HourMenu.selectedIndex].value;
                    var fcast_lead_value = LeadMenu.options[LeadMenu.selectedIndex--].value;
                    var pr_threshold_value = PrThresholdMenu.options[PrThresholdMenu.selectedIndex].value;
                    var sp_threshold_value = SpThresholdMenu.options[SpThresholdMenu.selectedIndex].value;

                    src = \'""" + """./Cold_surge_EnsMean_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h.png';            
                    document.getElementById("ensmean_image").src = src;

                    src = \'""" + """./Cold_surge_ProbMaps_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h_Pr'+pr_threshold_value+'_Sp'+sp_threshold_value+'.png';      
                    document.getElementById("prob_image").src = src;
            }
            </script>
            """
    html += """
                </div>
                <script>
                function nextLeadTime() {
                    var date_value = DateMenu.options[DateMenu.selectedIndex].value;
                    var hour_value = HourMenu.options[HourMenu.selectedIndex].value;
                    var fcast_lead_value = LeadMenu.options[LeadMenu.selectedIndex++].value;
                    var pr_threshold_value = PrThresholdMenu.options[PrThresholdMenu.selectedIndex].value;
                    var sp_threshold_value = SpThresholdMenu.options[SpThresholdMenu.selectedIndex].value;

                    src = \'""" + """./Cold_surge_EnsMean_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h.png';       
                    document.getElementById("ensmean_image").src = src;

                    src = \'""" + """./Cold_surge_ProbMaps_'+date_value+'_'+hour_value+'_T'+fcast_lead_value+'h_Pr'+pr_threshold_value+'_Sp'+sp_threshold_value+'.png';      
                    document.getElementById("prob_image").src = src;
            }
                </script>
                """

    html +="""
    
<p>Monitoring tool for north-easterly cold surges from MOGREPS ensemble forecasts. Ensemble mean plots from 36 
    member
    ensemble is generated for 24 hour accumulated precipitation and 850 hPa winds. Cold surge probabilities are 
    calculated based
    on Chang et al (2015) with northeasterly winds with wind speed over 9 m/s averaged over 5-10N 107-115E. 
    
    If the cold surge
    crosses the equator over 5S-5N, 105-115E with speed exceeding 2 m/s it is categorised as cross equatorial surge. 
    Probability
    maps of precipitation and wind speed exceeding a number of thresholds are also shown.
    
    </p>
    
    
    <p>Chang, C.-P., P. A. Harr, and H. J. Chen, 2005a: Synoptic disturbances over the equatorial South China 
    Sea and western Maritime Continent during boreal winter. Mon. Wea. Rev., 133, 489-503</p>
    
    <p>Hattori, M., S. Mori, and J. Matsumoto, 2011: The cross-equatorial northerly surge over the Maritime Continent 
    and its relationship to precipitation patterns. J. Meteor. Soc. Japan, 89A, 27-47.</p>

    <p> 
    </p>"""



    html += """
    </body>
    </html>
    """
    #print(html)

    file_html = open(os.path.join(fig_dir, 'CS_static.html'), 'w')
    file_html.write(html)
    file_html.close()
    print('%s is written. ' % file_html.name)


if __name__ == '__main__':
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    hours = [0]  # [0, 6, 12, 18]
    for hour in hours:
        yesterday = datetime.datetime(2020, 11, 22, hour, 0)
        # yesterday = datetime.datetime(yesterday.year,
        #                              yesterday.month,
        #                              yesterday.day, hour, 0)
        write_html_page_instantaneous(yesterday)
