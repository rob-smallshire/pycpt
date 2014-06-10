__author__ = 'rjs'

from collections import namedtuple

CommentNode = namedtuple('CommentNode', ['comment'])
ColorModelNode = namedtuple('ColorModelNode', ['model', 'interpolation'])
TripletNode = namedtuple('TripletNode', ['first', 'second', 'third'])
CMYKColorNode = namedtuple('CMYKColorNode', ['cyan', 'magenta', 'yellow', 'key'])
GrayColorNode = namedtuple('GrayColorNode', ['level'])
RGBColorNode = namedtuple('RGBColorNode', ['red', 'green', 'blue'])
HSVColorNode = namedtuple('HSVColorNode', ['hue', 'saturation', 'value'])
NamedColorNode = namedtuple('NamedColorNode', ['name'])
CategoryNode = namedtuple('CategoryNode', ['category', 'color'])


class IntervalSpecNode(object):

    def __init__(self, lower_z, lower_color, upper_z, upper_color,
                 annotation=None, label=None, interpolation_color_model='rgb'):
        self.lower_z = lower_z
        self.lower_color = lower_color
        self.upper_z = upper_z
        self.upper_color = upper_color
        self.annotation = annotation
        self.label = label
        self.interpolation_color_model = interpolation_color_model
