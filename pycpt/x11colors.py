import os
import logging

from colors import RGBColor

log = logging.getLogger("cpt.x11colors")

DICTIONARY_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rgb.txt')
log.debug("DICTIONARY_FILENAME = {0}".format(DICTIONARY_FILENAME))

_colors = None

def _load_colors():
    '''
    Load the color dictionary
    '''
    global _colors
    _colors = {}
    with open(DICTIONARY_FILENAME) as f:
        for line in f:
            fields = line.split()
            if len(fields) == 4:
                try:
                    color = (int(fields[0]), int(fields[1]), int(fields[2]))
                except ValueError:
                    log.warning('Could not read valid color from "{0}"'.format(line))
                    continue
                name = fields[3]
                normalised_name = _normalise(name)
                if normalised_name in _colors:
                    log.warning('Duplicate color {0} defined for {1}'.format(name, normalised_name))
                _colors[normalised_name] = color

def _normalise(name):
    '''
    Normalise a name to a canonical format.
    '''
    return name.replace(' ', '').lower()

def named_color(name):
    global _colors
    if _colors is None:
        _load_colors()

    normalised_name = _normalise(name)

    try:
        return _colors[normalised_name]
    except KeyError:
        raise ValueError("No such named color.")



    
        

  