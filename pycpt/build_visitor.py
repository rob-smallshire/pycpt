import logging
from pycpt.cpt import (Boundary, Interval, ANNOTATE_NEITHER, ANNOTATE_BOTH,
                       ANNOTATE_LOWER, ANNOTATE_UPPER, ColorPaletteTable)

log = logging.getLogger('pycpt.build_visitor')

class BuildVisitor(object):
    def __init__(self):
        self._cpt = ColorPaletteTable()
        self._description = []

    cpt = property(lambda self: self._cpt)

    def visit(self, node, *args, **kwargs):
        meth = None
        for cls in node.__class__.__mro__:
            meth_name = 'visit_'+cls.__name__
            meth = getattr(self, meth_name, None)
            if meth:
                break

        if not meth:
            meth = self.generic_visit
        return meth(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        log.debug('generic_visit ' + node.__class__.__name__)

    ANNOTATION_CODE = { None: ANNOTATE_NEITHER,
                      'U': ANNOTATE_UPPER,
                      'L': ANNOTATE_LOWER,
                      'B': ANNOTATE_BOTH }

    def visit_CommentNode(self, node):
        log.debug('visit_CommentNode')
        self._description.append(node.comment)


    def visit_IntervalSpecNode(self, node):
        log.debug('visit_IntervalSpecNode')
        interval = Interval(Boundary(node.lower_z, node.lower_color),
                            Boundary(node.upper_z, node.upper_color),
                            BuildVisitor.ANNOTATION_CODE[node.annotation],
                            node.label,
                            node.interpolation_color_model)
        self._cpt.append(interval)

    CATEGORY_CODE = { 'F': "foreground_color",
                      'B': "background_color",
                      'N': "nan_color" }

    def visit_CategoryNode(self, node):
        setattr(self._cpt, BuildVisitor.CATEGORY_CODE[node.category], node.color)


