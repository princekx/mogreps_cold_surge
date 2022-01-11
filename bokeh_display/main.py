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

def get_dates():
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    print(fcast_in_dir)
    dum_dates = glob.glob('%s/*/*/*' %fcast_in_dir)
    dates = []
    for dum in dum_dates:
        dates.append(dum[-10:])
    return sorted(dates)

def get_members(date_to_plot):
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    dum_members = glob.glob('%s/%s/*' %(fcast_in_dir, date_to_plot))
    members = []
    for dum in dum_members:
        members.append(dum[-3:])
    return sorted(members)

def get_lead_time(date_to_plot, member_to_plot):
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    dum_leads = glob.glob('%s/%s/%s/*' % (fcast_in_dir, date_to_plot, member_to_plot))
    leads = []
    for dum in dum_leads:
        leads.append(dum[-6:-3])
    return sorted(leads)

def plot_data(ucube, vcube, precip):

    lons = ucube.coord('longitude').points
    lats = ucube.coord('latitude').points

    # flip data around dateline
    # lons = np.array(lons)
    # ind = np.where(lons <= 180.)[0][-1]
    # print ind, lons[ind]
    # cube1 = olr_cube.copy()
    # cube1.data[:, :] = 0.
    # cube1.data[:, :ind] = olr_cube.data[:, ind:]
    # cube1.data[:, ind:] = olr_cube.data[:, :ind]

    # lons[np.where(lons > 180.)] = lons[np.where(lons > 180.)] - 360.
    # cube1.coord('longitude').points = np.sort(lons)
    # Linear
    color_mapper = LinearColorMapper(palette=GnBu9, low=0, high=50)
    # Log mapper
    #color_mapper = LogColorMapper(palette=GnBu9, low=10, high=300)

    # coastlines
    with open(os.path.join(os.path.dirname(__file__), 'data/countries.geo.json'), 'r') as f:
        countries = GeoJSONDataSource(geojson=f.read())

    plot.image(image=[precip.data], x=70, y=-20, dw=80, dh=50, color_mapper=color_mapper, alpha=0.5)
    plot.patches("xs", "ys", color=None, line_color="black", source=countries)

    # Vectors
    x0, y0, x1, y1, xR, yR, xL, yL, length = winds.arrows(lons, lats, ucube.data, vcube.data,
                                                          density=5, maxspeed=5, arrowLength=2, arrowHeadAngle=10)

    #cm = np.array(["#C7E9B4", "#7FCDBB", "#41B6C4", "#1D91C0", "#225EA8", "#0C2C84"])
    cm = np.array(Magma6)
    ix = ((length - length.min()) / (length.max() - length.min()) * 5).astype('int')

    colors = cm[ix]

    #colors = 'black'
    plot.segment(x0, y0, x1, y1, color=colors, line_width=1, alpha=0.5)
    plot.segment(x1, y1, xR, yR, color=colors, line_width=1, alpha=0.5)
    plot.segment(x1, y1, xL, yL, color=colors, line_width=1, alpha=0.5)

    plot.background_fill_color = "white"
    plot.x_range = Range1d(start=70, end=150)
    plot.y_range = Range1d(start=-20, end=30)

    title = 'Winds 850, precip Forecast reference time: %s Forecast period: %s H Valid on: %s'\
            %(str(ucube.coord('forecast_reference_time'))[10:29],
              str(ucube.coord('forecast_period').points[0]),
              str(ucube.coord('time'))[10:20])
    plot.title.text = title
    plot.title.text_font_size = "17px"
    print(type(title))

    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12,
                         border_line_color=None, location=(0, 0),
                         orientation='horizontal')
    return plot, color_bar

def get_data(sdate, smember, slead):
    fcast_in_dir = data_paths.dirs('mog_forecast_data_dir')
    data_file = os.path.join(fcast_in_dir, sdate, smember,'englaa_pd%s.pp' % slead)
    print(data_file)
    ucube = iris.load_cube(data_file, 'x_wind')
    ucube = ucube.extract(iris.Constraint(pressure=850))
    vcube = iris.load_cube(data_file, 'y_wind')
    vcube = vcube.extract(iris.Constraint(pressure=850))

    if slead != '000':
        slead_minus_24 = str('%03d' % (int(slead) - 24))
        data_file_minus_24 = os.path.join(fcast_in_dir, sdate, smember,'englaa_pd%s.pp' % slead_minus_24)
        precip = iris.load_cube(data_file, 'precipitation_amount')
        precip_m24 = iris.load_cube(data_file_minus_24, 'precipitation_amount')
        precip -= precip_m24
    else:
        precip = iris.load_cube(data_file, 'precipitation_amount')
        #precip *= 8.

    ucube = ucube.intersection(latitude=(-20, 30), longitude=(70, 150))
    vcube = vcube.intersection(latitude=(-20, 30), longitude=(70, 150))

    # interpolate to the same grid
    ucube = ucube.regrid(vcube, iris.analysis.Linear())

    precip = precip.intersection(latitude=(-20, 30), longitude=(70, 150))

    '''
    import matplotlib.pyplot as plt
    import iris.quickplot as qplt
    qplt.contourf(precip, levels=[10,20, 30, 40, 50, 60])
    plt.savefig('p.png')
    '''

    return ucube, vcube, precip

def update_plot(attrname, old, new):
    ucube, vcube, precip = get_data(date_select.value,
                            member_select.value,
                            lead_select.value)
    # Draw plot
    plot, color_bar = plot_data(ucube, vcube, precip)
    #plot.add_layout(color_bar, 'below')

#def main(page_name):

# Get available data dates and data for the first
# available date to plot as a start
# 1. DATE SELECT MENU
menu_dates = get_dates()
selected_date = menu_dates[-2]

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
