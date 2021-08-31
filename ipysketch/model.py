
class SketchModel(object):

    def __init__(self, name):
        self.paths = []
        self.current_path = None
        self.name = name
        print('Init model')

    def start_path(self, x, y, pen):
        path = Path(pen)
        path.add_point(x, y)
        self.current_path = path

    def add_to_path(self, x, y):
        if self.current_path:
            self.current_path.add_point(x, y)

    def finish_path(self):
        if self.current_path is None:
            return
        self.paths.append(self.current_path)
        self.current_path = None

    def remove(self, path):
        self.paths.remove(path)

    def find_paths(self, x, y, radius):
        found = []
        circle = Circle((x, y), radius)
        for p in self.paths:
            for point in p.points:
                if circle.contains(point):
                    found.append(p)
                    break
        return found

    def clear(self):
        self.paths = []

    def get_bounding_box(self):
        # TODO: Make this dynamic later to fit the image size to the actual sketch boundaries
        # Idea: find the bounding box for the sketch, then save only the content of the bounding box
        #       as an image
        minx, miny = 1E9, 1E9
        maxx, maxy = -1E9, -1E9
        for path in self.paths:
            for point in path.points:
                if point[0] < minx:
                    minx = point[0]
                if point[0] > maxx:
                    maxx = point[0]
                if point[1] < miny:
                    miny = point[1]
                if point[1] > maxy:
                    maxy = point[1]
        return (minx, miny), (maxx, maxy)


class Pen(object):

    def __init__(self, width=1, color='#000000'):
        self.width = width
        self.color = color


class Circle(object):

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def contains(self, point):
        return (self.center[0] - point[0])**2 + (self.center[1] - point[1])**2 < self.radius**2

    def upper_left(self):
        return self.center[0] - self.radius, self.center[1] + self.radius

    def lower_right(self):
        return self.center[0] + self.radius, self.center[1] - self.radius


class Path(object):

    def __init__(self, pen=None):
        if not pen:
            pen = Pen()
        self.pen = pen
        self.points = []

    def add_point(self, x, y):
        self.points.append((x, y))

    def lines(self):
        '''Enumerate lines in path'''
        lines = []
        for i in range(1, len(self.points)):
            line = self.points[i-1], self.points[i]
            lines.append(line)
        return lines

    def lines_flat(self):
        lines = []
        for i in range(1, len(self.points)):
            line = [self.points[i-1][0], self.points[i-1][1], self.points[i][0], self.points[i][1]]
            lines.append(line)
        return lines

    def points_flattened(self):
        flat_list = []
        for pt in self.points:
            flat_list.extend([pt[0], pt[1]])
        return tuple(flat_list)
