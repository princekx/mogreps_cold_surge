import math
import numpy as np
from bokeh.palettes import Viridis11

class vector():
    '''
    Generates vectors for plotting winds.
    '''

    def __init__(self, u, v, **kwargs):
        '''
        '''
        # Get arguments
        xSkip = kwargs.get("xSkip", 2)
        ySkip = kwargs.get("ySkip", 2)
        maxSpeed = kwargs.get("maxSpeed", 20.)
        arrowHeadAngle = kwargs.get("arrowHeadAngle", 35.)
        arrowHeadScale = kwargs.get("arrowHeadScale", 1.)
        arrowType = kwargs.get("arrowType", "barbed")
        palette = kwargs.get('palette', Viridis11)
        palette_reverse = kwargs.get('palette_reverse', False)

        if palette_reverse:
            palette.reverse()

        u = u[::ySkip, ::xSkip]
        v = v[::ySkip, ::xSkip]

        x = u.coord('longitude').points
        y = u.coord('latitude').points
        U = u.data
        V = v.data

        X, Y = np.meshgrid(x, y)
        speed = np.sqrt(U * U + V * V)

        # theta = np.arctan2(U, V)
        # r2d = 45.0 / math.atan(1.0)
        # theta = np.arctan2(U, V) + 45.*np.pi/180.
        # theta = -(np.arctan2(U, V) + np.pi / 2)
        # as per matplotlib.quiver code
        theta = np.arctan2(V, U)

        x0 = X.flatten()
        y0 = Y.flatten()
        length = speed.flatten() / maxSpeed
        angle = theta.flatten()
        x1 = x0 + length * np.cos(angle)
        y1 = y0 + length * np.sin(angle)

        # Colors
        cm = np.array(palette)
        # ix = ((length - length.min()) / (length.max() - length.min()) * (maxSpeed)).astype('int')
        ix = [int(i) for i in np.interp(length, (length.min(), length.max()), (0, len(cm) - 1))]

        self.colors = cm[ix]
        # print(min(ix), max(ix), len(cm))

        dx = x1 - x0
        dy = y1 - y0

        rad = math.radians(arrowHeadAngle)  # ; //35 angle, can be adjusted
        # This is for Kite shaped arrows
        xR = x1 - arrowHeadScale * length * np.cos(angle + rad)
        yR = y1 - arrowHeadScale * length * np.sin(angle + rad)

        xL = x1 - arrowHeadScale * length * np.cos(angle - rad)
        yL = y1 - arrowHeadScale * length * np.sin(angle - rad)

        if arrowType in ['kite', 'Kite', 'KITE']:
            self.xs = [[x1[i], xR[i], x0[i], xL[i], x1[i]] for i in range(len(x0))]
            self.ys = [[y1[i], yR[i], y0[i], yL[i], y1[i]] for i in range(len(y0))]

        if arrowType in ['barbed', 'Barbed', 'BARBED']:
            # for barbed arrows -->
            xR1 = x1 - arrowHeadScale * length * 0.5 * np.cos(angle + rad * 0.5)
            yR1 = y1 - arrowHeadScale * length * 0.5 * np.sin(angle + rad * 0.5)

            xL1 = x1 - arrowHeadScale * length * 0.5 * np.cos(angle - rad * 0.5)
            yL1 = y1 - arrowHeadScale * length * 0.5 * np.sin(angle - rad * 0.5)

            self.xs = [[x1[i], xR[i], xR1[i], x0[i], xL1[i], xL[i], x1[i]] for i in range(len(x0))]
            self.ys = [[y1[i], yR[i], yR1[i], y0[i], yL1[i], yL[i], y1[i]] for i in range(len(y0))]