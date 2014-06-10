__author__ = 'rjs'

import sys
current_module = sys.modules[__name__]

def convert(color, color_model):
    func = getattr(current_module, 'convert_to_' + color_model)
    return func(color)

def convert_to_rgb(color):
    pass

def convert_to_hsv(color):
    pass

def convert_to_cmyk(color):
    pass


  