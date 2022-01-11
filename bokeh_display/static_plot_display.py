import glob
import os
import sys
from bokeh.layouts import row, column, widgetbox
from bokeh.plotting import figure, show
from bokeh.io import curdoc, output_file, show
from bokeh.models import ColumnDataSource, HoverTool, Select
from bokeh.models import  Range1d, LinearColorMapper, ColorBar, LogColorMapper
from bokeh.models import GeoJSONDataSource
from bokeh.palettes import GnBu9, Magma6

import libs.bokeh_winds as winds
import numpy as np
import iris

import codes.data_paths as data_paths

# reverse colorbar
GnBu9.reverse()
Magma6.reverse()

def get_plot_metadata():
    plot_ens_dir = data_paths.dirs('plot_ens_html')
    dum_dates = glob.glob('%s/*.html' %plot_ens_dir)
    print(dum_dates)
    dates = []
    for dum in dum_dates:
        dates.append(dum[-10:])
    return sorted(dates)


#def main(page_name):

# Get available data dates and data for the first
# available date to plot as a start
# 1. DATE SELECT MENU
menu_dates = get_dates()

sys.exit()
selected_date = menu_dates[-1]

# set up a drop down menu of available dates
date_select = Select(value=selected_date, title='Date:', options=menu_dates)

# set up a drop down menu of available members
# 2 MEMBER SELECT MENU
members = get_members(date_select.value)
selected_member = members[0]
member_select = Select(value=selected_member, title='Ens Member:', options=sorted(members))

# set up a drop down menu of available members
# 3 Lead Time SELECT MENU
leads = get_lead_time(date_select.value, member_select.value)
selected_lead = '024'#leads[0]
lead_select = Select(value=selected_lead, title='Lead Time:', options=sorted(leads))

plot = figure(plot_height=800, plot_width=1100, title='',
               tools=["pan, reset, save, box_zoom, wheel_zoom, hover"],
              x_axis_label='Longitude', y_axis_label='Latitude')

ucube, vcube, precip = get_data(date_select.value,
                        member_select.value,
                        lead_select.value)
# Draw plot
plot, color_bar = plot_data(ucube, vcube, precip)
plot.add_layout(color_bar, 'below')

# Menus
date_select.on_change('value', update_plot)
member_select.on_change('value', update_plot)
lead_select.on_change('value', update_plot)

controls = column(date_select, member_select, lead_select)


# Draw the first plot





#desc = Div(text=open(os.path.join(os.path.dirname(__file__), "description.html")).read(), width=1600)
#sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example

#plots = gridplot([[plot_gl, plot_mog]])
#page_layout = layout([[desc], [controls, plots], ], sizing_mode=sizing_mode)
curdoc().add_root(row(controls, plot))
#curdoc().add_root(row(controls))
curdoc().title = "MOGREPS Cold Surge Monitor"
