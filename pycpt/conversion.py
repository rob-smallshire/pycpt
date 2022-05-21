import sys

from pycpt.colors import RGBColor, HSVColor, CMYKColor


current_module = sys.modules[__name__]


def convert_color(color, color_model):
    func = getattr(current_module, 'convert_to_' + color_model)
    return func(color)


def convert_to_rgb(color):
    if isinstance(color, RGBColor):
        return color
    raise NotImplementedError


def convert_to_hsv(color):
    if isinstance(color, HSVColor):
        return color
    raise NotImplementedError


def convert_to_cmyk(color):
    if isinstance(color, CMYKColor):
        return color
    raise NotImplementedError

