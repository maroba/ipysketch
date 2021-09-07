from copy import deepcopy
from shapely.geometry import Point as shPoint
from shapely.geometry.polygon import Polygon
import uuid
from scipy.interpolate import interp1d
import numpy as np


class SketchModel(object):
    """
    Represents the data of a complete sketch
    """

    def __init__(self, name):
        """
        Initializes a sketch.

        :param name: (str) Name of the sketch. Is used as file basename.

        """
        self.paths = []
        self.name = name
        self.dirty = True

    def clone(self):
        return deepcopy(self)

    def start_path(self, x, y, pen):
        """ Add a new path to the model.

        :param x: starting point x-coordinate
        :param y: starting point y-coordinate
        :param pen: the Pen object to use
        :return:
        """
        path = Path(pen)
        path.add_point(x, y)
        self.paths.append(path)

    @property
    def current_path(self):
        """ Returns the latest added path.

        :return: Path
        """
        if self.paths:
            return self.paths[-1]

    def add_to_path(self, x, y):
        """ Adds a point to the currently active path.

        :param x: x-coordinate
        :param y: y-coordinate
        :return:
        """
        if self.current_path:
            self.current_path.add_point(x, y)

    def remove(self, path):
        """ Remove a path from the sketch.

        :param path: Path object to remove
        :return:
        """
        self.paths.remove(path)

    def find_paths(self, x, y, radius):
        """ Find all paths in the sketch that cross circle around given point.

        :param x: x-coordinate of the point
        :param y: y-coordinate of the point
        :param radius: radius of the circle
        :return: list of found Path objects
        """
        found = []
        circle = Circle((x, y), radius)
        for p in self.paths:
            for point in p.points:
                if circle.contains(point):
                    found.append(p)
                    break
        return found

    def clear(self):
        """ Clears the sketch of all paths """
        self.paths = []

    def get_bounding_box(self):
        """ Get a bounding box around the actual sketched objects."""

        minx, miny = 1E9, 1E9
        maxx, maxy = -1E9, -1E9
        for path in self.paths:
            for point in path.points:
                if point.x < minx:
                    minx = point.x
                if point.x > maxx:
                    maxx = point.x
                if point.y < miny:
                    miny = point.y
                if point.y > maxy:
                    maxy = point.y
        return Point((minx, miny)), Point((maxx, maxy))

    def filter_by_uuids(self, uuids):
        """ Filter the paths in the model by a list of UUIDs

        :param uuids: list of (str)-UUIDs
        :return: list of Path objects
        """

        filtered = []
        for path in self.paths:
            if path.uuid in uuids:
                filtered.append(path)
        return filtered


class Pen(object):
    """
    Class representing the pen used for drawing.
    """

    def __init__(self, width=1, color='#000000'):
        """

        :param width: width of the pen (int)
        :param color: color of the pen (6 digit hex-valued code as str)
        """
        self.width = width
        self.color = color
        self.dash = None

    def clone(self):
        return Pen(self.width, self.color)

    def __repr__(self):
        repr = 'Line width: %d\n' % self.width
        repr += 'Color: %s\n' % self.color
        repr += 'Dash: %s\n\n' % self.dash
        return repr


class Point(object):
    """
    Represents a point in the sketch.
    """

    def __init__(self, *args):
        """
        Initializes Point.

        :param args: either a 2-tuple with x and y coordinates or
                x and y coordinate separately

        Points can be added and subtracted as well as be multiplied by numbers.
        """
        self.xy = list(*args)

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
        p = Point(self.xy)
        p.x += other.x
        p.y += other.y
        return p

    def __sub__(self, other):
        p = Point(self.xy)
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


class Vector(Point):
    """
    Just an alias for Point.
    """
    def __init__(self, *args):
        super(Vector, self).__init__(*args)


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


class Path(object):
    """
    Representation of a continuous path.
    """

    def __init__(self, pen=None):
        if not pen:
            pen = Pen()
        self.uuid = str(uuid.uuid4())
        self.pen = pen
        self.points = []
        self.offset = Point((0, 0))

    def add_point(self, x, y):
        """ Add a point to the end of the path

        :param x: x-coordinate
        :param y: y-coordinate
        :return:
        """
        p = Point((x, y))
        self.points.append(p)

    def smoothed_points(self):
        points = np.array([(p.x, p.y) for p in self.points])
        xx = points[:, 0]
        yy = points[:, 1]

        sigma = [0.]

        for i in range(1, len(xx)):
            ds2 = (xx[i] - xx[i - 1]) ** 2 + (yy[i] - yy[i - 1]) ** 2
            s = sigma[-1] + np.sqrt(ds2)
            sigma.append(s)

        xfunc = interp1d(sigma, xx, kind='cubic')
        yfunc = interp1d(sigma, yy, kind='cubic')

        sigma_dense = np.arange(0, sigma[-1], 1)
        x_dense = xfunc(sigma_dense)
        y_dense = yfunc(sigma_dense)
        return [Point((x, y)) for x, y in zip(x_dense, y_dense)]

    def lines(self):
        """ Returns a list of line segments between the points in the path

        :return: list of Point 2-tuples
        """
        lines = []
        for i in range(1, len(self.points)):
            line = self.points[i-1], self.points[i]
            lines.append(line)
        return lines

    def lines_flat(self):
        """ Same as lines(self), but with the Point objects flattened to x, y

        :return: list of coordinates (x0, y0, x1, y1, x2, y2, ...)
        """
        lines = []
        points = [p + self.offset for p in self.points]
        for i in range(1, len(points)):
            line = [points[i-1][0], points[i-1][1], points[i][0], points[i][1]]
            lines.append(line)
        return lines

    def points_flattened(self):
        flat_list = []
        points = [p + self.offset for p in self.points]
        for pt in points:
            flat_list.extend([pt[0], pt[1]])
        return tuple(flat_list)

    def contains(self, point):
        """ Treating the path as closed (connecting first an last points), check if point is contained in
            resulting polygon.

        :param point: Point
        :return:
        """

        # Close path creating a polygon
        try:
            pt = shPoint(point.x, point.y)
            polygon = Polygon((p.x, p.y) for p in self.points)
            return polygon.contains(pt)
        except:
            pass

    def overlaps(self, circle):
        """ Check if the path overlaps with a circle.

        :param circle: Circle
        :return:
        """
        for pt in self.points:
            if circle.contains(pt):
                return True
        return False

    def apply_offset(self):
        for i, p in enumerate(self.points):
            self.points[i] = p + self.offset
        self.offset = Point((0, 0))

    def __repr__(self):
        repr = 'Path UUID: %s\n' % self.uuid
        repr += 'Number of points: %d\n' % len(self.points)
        repr += 'Pen: \n' + str(self.pen)
        repr += 'Points: \n'
        for p in self.points:
            repr += str(p) + ', '
        return repr


def flatten(points):
    flat_list = []
    for pt in points:
        flat_list.extend([pt[0], pt[1]])
    return tuple(flat_list)