'''
Support for Colour Palette Tables as modelled by the Generic Mapping Tools.

http://gmt.soest.hawaii.edu/gmt/html/GMT_Docs.html#x1-720004.15
'''

import math

from pycpt.colors import RGBColor
from pycpt.conversion import convert_color

__author__ = 'rjs'

# Colour space information for GMT
# http://gmt.soest.hawaii.edu/gmt/html/GMT_Docs.html#x1-212000I

ANNOTATE_NEITHER = 0
ANNOTATE_LOWER = 1
ANNOTATE_UPPER = 2
ANNOTATE_BOTH  = 3


def lerp(x1, y1, x2, y2, x):
    '''Linear interpolation'''
    m = (y2 - y1) / (x2 / x1)
    c = y1 - m * x1
    y = m * x + c
    return y


class Boundary(object):
    '''The boundary of an interval comprising a value and a color.'''
    def __init__(self, value, color):
        self.value = value
        self.color = color


class Interval(object):
    '''
    A coloured interval with defined by two values with corresponding colours.
    '''
    def __init__(self, lower_boundary, upper_boundary, annotate=ANNOTATE_NEITHER, label=None, interpolation_color_model='rgb'):
        if lower_boundary.value > upper_boundary.value:
            raise ValueError("lower_boundary must me lower than upper_boundary")
        self.lower_boundary = lower_boundary
        self.upper_boundary = upper_boundary
        self.annotate = annotate
        self.label = label
        self.interpolation_color_model = interpolation_color_model

    def interpolate(self, value):
        if not (self.lower_boundary.value <= value <= self.upper_boundary.value):
            message = "value {0} not in range {1} to {1}".format(value,
                          self.lower_boundary.value, self.upper_boundary.value)
            raise ValueError(message)

        assert type(self.lower_boundary) == type(self.upper_boundary)

        T = type(self.lower_boundary)
        result = T(*(lerp(self.lower_boundary.value, lower_channel,
                          self.upper_boundary.value, upper_channel,
                          value)
                   for lower_channel, upper_channel in zip(self.lower_boundary.color,
                                                           self.upper_boundary.color)))
        return result

        
class ColorPaletteTable(object):
    '''A function to map from values to colours.

    The domain of the function is mapped through inclusive intervals. Intervals
    may overlap and the first interval to found to contain a value 'wins'
    '''

    def __init__(self, intervals=None, background_color=None,
                 foreground_color=None, nan_color=None, color_model='rgb',
                 description=''):
        '''
        Create a ColourPaletteTable.

        Args:
            intervals: A iterable of Intervals.

            background_color: The color to be used for values less than the
                lowest interval. Defaults to black.

            foreground_color: The color to be used for values greater than the
                highest interval. Defaults to white.

            nan_color: The color to be used for NaN values. Defaults to gray.

            color_model: One of 'rgb', 'hsv' or 'cmyk'.  The color model in
                which interpolated values are to be returned. Defauts to 'rgb'

            description: An optional description string.
        '''
        self.intervals = list(intervals) if intervals is not None else []
        self.background_color = background_color if background_color is not None else RGBColor(0, 0, 0)
        self.foreground_color = foreground_color if foreground_color is not None else RGBColor(255, 255, 255)
        self.nan_color = nan_color if nan_color is not None else RGBColor(127, 127, 127)
        self.color_model = color_model
        self.description = description

    def __len__(self):
        return len(self.intervals)

    def _interpolate(self, value):
        if math.isnan(value):
            return self.nan_color
        min_value = None
        max_value = None
        for interval in self.intervals:
            if interval.lower_boundary <= value <= interval.upper_boundary:
                return interval.interpolate(value)
            min_value = min(min_value, interval.lower_boundary)
            max_value = max(max_value, interval.upper_boundary)
        if value < min_value:
            return self.background_color
        assert value > max_value
        return self.foreground_color

    def interpolate(self, value, color_model=None):
        if color_model is None:
            color_model = self.color_model
        color = self._interpolate(value)
        return convert_color(color, color_model)

    def __call__(self, value):
        return self.interpolate(value)

    def append(self, interval):
        self.intervals.append(interval)


        
  