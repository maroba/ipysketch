from copy import deepcopy
import uuid

from shapely.geometry import Point as shPoint
from shapely.geometry.polygon import Polygon


class History(object):

    def __init__(self, initial_model):
        self.models = [initial_model]
        self._model_ptr = 0

    def current(self):
        return self.models[self._model_ptr]

    def append(self, model):
        self.models.append(model)
        self._model_ptr += 1

    def last(self):
        return self.models[-1]

    def new(self):
        if self._model_ptr != len(self.models) - 1:
            self.models = self.models[:self._model_ptr + 1]
        self.append(self.last().clone())

    def back(self):
        if self._model_ptr > 0:
            self._model_ptr -= 1

    def forward(self):
        if self._model_ptr < len(self.models) - 1:
            self._model_ptr += 1

    def __repr__(self):
        return '# models: %d, current model idx: %d' % (len(self.models), self._model_ptr)


class SketchModel(object):

    def __init__(self):
        self.paths = []
        self.lasso = None

    def clone(self):
        return deepcopy(self)

    def start_path(self, point, pen=None):
        pen = pen or Pen()
        path = Path(pen)
        path.append(point)
        self.paths.append(path)

    def continue_path(self, point):
        path = self.paths[-1]
        path.append(point)

    def finish_path(self, point):
        path = self.paths[-1]
        path.append(point)

    def erase_paths(self, paths):
        for path in paths:
            self.remove(path)

    def start_lasso(self, point):
        self.lasso = Lasso()
        self.lasso.append(point)

    def continue_lasso(self, point):
        self.lasso.append(point)

    def finish_lasso(self, point):
        self.lasso.append(point)
        self.lasso.append(self.lasso.points[0])
        selection = []
        for path in self.paths:
            if self.lasso.contains(path):
                selection.append(path)
        self.lasso = None
        return selection

    def bbox(self):

        minx = miny = 1E9
        maxx = maxy = -1E9

        for path in self.paths:
            for pt in path.points:
                if pt.x < minx:
                    minx = pt.x
                if pt.y < miny:
                    miny = pt.y
                if pt.x > maxx:
                    maxx = pt.x
                if pt.y > maxy:
                    maxy = pt.y

        return Rectangle(Point(minx, miny), Point(maxx, maxy))

    def remove(self, path):
        for p in self.paths:
            if p.uuid == path.uuid:
                self.paths.remove(p)


class Path(object):

    def __init__(self, pen=None):
        self.pen = pen or Pen()
        self.points = []
        self.uuid = str(uuid.uuid4())

    def clone(self):
        return deepcopy(self)

    def append(self, point):
        self.points.append(point)

    def translate(self, vector):
        for i, _ in enumerate(self.points):
            self.points[i] += vector


class Lasso(Path):

    def __init__(self):
        pen = Pen(dash=(5,3))
        super().__init__(pen)

    def contains(self, path):

        polygon = Polygon((p.x, p.y) for p in self.points)

        for point in path.points:
            pt = shPoint(point.x, point.y)
            if polygon.contains(pt):
                return True
        return False


class Pen(object):
    """
    Class representing the pen used for drawing.
    """

    def __init__(self, width=1, color='#000000', dash=None):
        """

        :param width: width of the pen (int)
        :param color: color of the pen (6 digit hex-valued code as str)
        """
        self.width = width
        self.color = color
        self.dash = dash

    def clone(self):
        return Pen(self.width, self.color)

    def __repr__(self):
        repr = 'Line width: %d\n' % self.width
        repr += 'Color: %s\n' % self.color
        repr += 'Dash: %s\n\n' % self.dash
        return repr


class Rectangle(object):

    def __init__(self, upper_left, lower_right):
        self.ul = upper_left
        self.lr = lower_right


class Point(object):
    """
    Represents a point in the sketch.
    """

    def __init__(self, x, y):
        self.xy = [x, y]

    @property
    def x(self):
        return self.xy[0]

    @x.setter
    def x(self, value):
        self.xy[0] = value

    @property
    def y(self):
        return self.xy[1]

    @y.setter
    def y(self, value):
        self.xy[1] = value

    def __add__(self, other):
        p = Point(self.xy[0], self.xy[1])
        p.x += other.x
        p.y += other.y
        return p

    def __sub__(self, other):
        p = Point(self.xy[0], self.xy[1])
        p.x -= other.x
        p.y -= other.y
        return p

    def __mul__(self, other):
        assert not isinstance(other, Point)
        p = Point(self.xy)
        p.x *= other
        p.y *= other
        return p

    def __getitem__(self, idx):
        return self.xy[idx]

    def __setitem__(self, idx, value):
        self.xy[idx] = value

    def __repr__(self):
        return '(%f, %f)' % (self.x, self.y)


class Circle(object):
    """
    Utility class for some circle operations.
    """

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def contains(self, point):
        """ Check if a point is inside the circle.

        :param point: the Point object to check
        :return: True or False
        """
        return (self.center[0] - point[0])**2 + (self.center[1] - point[1])**2 < self.radius**2

    def upper_left(self):
        """ Returns the upper left corner of the bounding box of the circle.

        :return: Point
        """
        return Point((self.center[0] - self.radius, self.center[1] - self.radius))

    def lower_right(self):
        """ Returns the lower right corner of the bounding box of the circle.

        :return: Point
        """
        return Point((self.center[0] + self.radius, self.center[1] + self.radius))


def filter_paths(paths, at_point, radius=20):
    found_paths = []
    circle = Circle(at_point, radius)
    for path in paths:
        for pt in path.points:
            if circle.contains(pt):
                found_paths.append(path)
                break
    return found_paths


class Translation(object):

    def __init__(self, origin):
        self.origin = origin


def flatten(points):
    flat_list = []
    for pt in points:
        flat_list.extend([pt[0], pt[1]])
    return tuple(flat_list)