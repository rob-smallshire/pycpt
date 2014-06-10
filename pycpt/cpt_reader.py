import logging
import re
from pycpt.build_visitor import BuildVisitor
import x11colors

logger = logging.getLogger('pycpt.cpt_reader')

from pycpt.ast import (CommentNode, CategoryNode, RGBColorNode, HSVColorNode,
                       CMYKColorNode, IntervalSpecNode)

FLOAT_PATTERN = r'([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'
HEX_RGB_PATTERN = r'\#([0-9A-Fa-f]{6})\b'
LABEL_PATTERN = r';\s*(?P<label>.+)'
TRIPLE_PATTERN = r'{float}\s+{float}\s+{float}'.format(float=FLOAT_PATTERN)
CMYK_PATTERN = r'{float}\s+{float}\s+{float}\s+{float}'.format(float=FLOAT_PATTERN)
GRAY_PATTERN = FLOAT_PATTERN
NAME_PATTERN = r'[A-Za-z]\w+'
ANNOTATION_PATTERN = r'(?P<annotation>[ULB])'

SUBSTITUTIONS = { 'float' : FLOAT_PATTERN,
                  'triple' : TRIPLE_PATTERN,
                  'cmyk' : CMYK_PATTERN,
                  'gray' : GRAY_PATTERN,
                  'name' : NAME_PATTERN,
                  'label' : LABEL_PATTERN,
                  'hexrgb' : HEX_RGB_PATTERN,
                  'annotation' : ANNOTATION_PATTERN }

COMMENT_REGEX = re.compile(r'^\s*\#\s*(.*)')
COLOR_MODEL_REGEX = re.compile(r'^\s*\#\s*COLOR_MODEL\s*=\s*(\+?)\s*(HSV|RGB|CMYK)')

INTERVAL_FORMATS = [ ('triple', 'triple'),
                     ('triple', 'hexrgb'),
                     ('triple', 'float'),
                     ('cmyk',   'cmyk'),
                     ('cmyk',   'hexrgb'),
                     ('cmyk',   'name'),
                     ('gray',   'gray'),
                     ('gray',   'hexrgb'),
                     ('gray',   'name'),
                     ('hexrgb', 'hexrgb'),
                     ('hexrgb', 'cmyk'),
                     ('hexrgb', 'name'),
                     ('hexrgb', 'gray'),
                     ('name',   'name'),
                     ('name',   'hexrgb'),
                     ('name',   'triple'),
                     ('name',   'cmyk'),
                     ('name',   'gray') ]

def initialise_interval_regexes(interval_formats, substitutions):
    base_substitution = { 'value1'     : r'(?P<value1>{float})'.format(**substitutions),
                          'value2'     : r'(?P<value2>{float})'.format(**substitutions),
                          'annotation' : r'(?P<annotation>[ULB])',
                          'label'      : r';\s*(?P<label>.+)' }
    interval_regexes = []
    for type1, type2 in interval_formats:
        specific_substitutions = { 'color1' : r'(?P<color1>{type1})'.format(type1=substitutions[type1]),
                                   'color2' : r'(?P<color2>{type2})'.format(type2=substitutions[type2]) }
        specific_substitutions.update(base_substitution)
        interval_pattern = r'\s*{value1}\s+{color1}\s+{value2}\s+{color2}(\s+{annotation})?(\s+{label})?\s*$'.format(**specific_substitutions)
        interval_regex = re.compile(interval_pattern)
        interval_regexes.append(interval_regex)
    return interval_regexes


def initialise_category_regexes(category_formats, substitutions):
    category_regexes = []
    for type in category_formats:
        color_pattern = r'(?P<color>{type})'.format(type=substitutions[type])
        category_pattern = r'\s*(?P<category>[FBN])\s+{color}\s*$'.format(
            color=color_pattern)
        category_regex = re.compile(category_pattern)
        category_regexes.append(category_regex)
    return category_regexes

INTERVAL_REGEXES = initialise_interval_regexes(INTERVAL_FORMATS, SUBSTITUTIONS)

CATEGORY_FORMATS = set([type1 for type1, type2 in INTERVAL_FORMATS])

CATEGORY_REGEXES = initialise_category_regexes(CATEGORY_FORMATS, SUBSTITUTIONS)

PERMITTED_COLOR_MODELS = set(['rgb', 'hsv', 'cmyk'])

class CptReaderError(Exception):
    pass

class CptReader(object):

    def __init__(self, filename):
        self.statements = []
        self.color_model = 'RGB'
        self.interpolation_model = 'RGB'
        self.filename = filename
        self.readers = [ self._read_color_model,
                         self._read_comment,
                         self._read_interval,
                         self._read_category ]

    def _read_color_model(self, line):
        color_model_match = COLOR_MODEL_REGEX.match(line) # TODO Case-insensitive
        if color_model_match:
            color_model = color_model_match.group(2).lower()
            if color_model not in PERMITTED_COLOR_MODELS:
                message = "Unknown color model {0}".format(color_model)
                logging.warning(message)
                raise CptReaderError(message)
            self.color_model = color_model
            if color_model_match.group(1) == '+':
                self.interpolation_model = color_model
            return True
        return False

    def _read_comment(self, line):
        comment_match = COMMENT_REGEX.match(line)
        if comment_match:
            comment = CommentNode(comment_match.group(1))
            self.statements.append(comment)
            return True
        return False

    def _read_interval(self, line):
        for ((type1, type2), regex) in zip(INTERVAL_FORMATS, INTERVAL_REGEXES):
            interval_match = regex.match(line)
            if interval_match:
                value1 = float(interval_match.group('value1'))
                value2 = float(interval_match.group('value2'))

                color1_reader = getattr(self, '_read_' + type1)
                color1 = color1_reader(interval_match.group('color1'), self.color_model)

                color2_reader = getattr(self, '_read_' + type2)
                color2 = color2_reader(interval_match.group('color2'), self.color_model)

                annotation = interval_match.group('annotation')
                label = interval_match.group('label')

                interval = IntervalSpecNode(value1, color1, value2, color2,
                                            annotation, label, self.interpolation_model)
                self.statements.append(interval)
                return True
        return False

    def _read_category(self, line):
        for type, regex in zip(CATEGORY_FORMATS, CATEGORY_REGEXES):
            category_match = regex.match(line)
            if category_match:
                category_code = category_match.group('category')

                color_reader = getattr(self, '_read_' + type)
                color = color_reader(category_match.group('color'), self.color_model)

                category = CategoryNode(category_code, color)
                self.statements.append(category)
                return True
        return False

    @staticmethod
    def _read_float(s, color_model):
        value = float(s)
        return value

    @staticmethod
    def _read_triple(s, color_model):
        a, b, c = tuple(float(x) for x in s.split())
        if color_model == 'hsv':
            return HSVColorNode(a, b, c)
        if color_model == 'rgb':
            return RGBColorNode(a, b, c)
        logger.warning("Interpreting number triplet as RGB whilst {0} color model in force.".format(color_model))
        return RGBColorNode(a, b, c)

    @staticmethod
    def _read_hexrgb(s, color_model):
        r = int(s[0: 2], 16)
        g = int(s[2: 4], 16)
        b = int(s[4: 6], 16)
        return RGBColorNode(r, g, b)

    @staticmethod
    def _read_gray(s, color_model):
        a = float(s)
        if color_model == 'hsv':
            return HSVColorNode(0.0, 0.0, a / 255.0)
        if color_model == 'cmyk':
            return CMYKColorNode(0.0, 0.0, 0.0, a / 255.0)
        return RGBColorNode(a, a, a)

    @staticmethod
    def _read_cmyk(s, color_model):
        c, m, y, k = tuple(float(x) for x in s.split())
        if color_model != 'cmyk':
            logger.warning("Interpreting number quadruplet as CMYK whilst {0} color model in force". format(color_model))
        return CMYKColorNode(c, m, y, k)

    @staticmethod
    def _read_name(s, color_model):
        color = x11colors.named_color(s)
        return RGBColorNode(*color)
    
    def _read_line(self, line):
        for reader in self.readers:
            if reader(line):
                return True
        return False

    def read(self):
        with open(self.filename) as f:
            for line_num, line in enumerate(f):
                if not self._read_line(line):
                    message = "Syntax error in CPT file at line {0}".format(line_num + 1)
                    logger.error(message)
                    raise CptReaderError(message)

    def build(self):
        '''Build a ColourPaletteTable'''
        visitor = BuildVisitor()
        for statement in self.statements:
            visitor.visit(statement)
        return visitor.cpt


if __name__ == '__main__':
    reader = CptReader('/home/rjs/dev/pycpt/cpts/test.cpt')
    reader.read()
    cpt = reader.build()
    pass














        




  