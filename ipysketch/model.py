import os
import pathlib
import pickle

from PIL import Image, ImageDraw


class SketchModel(object):

    def __init__(self):
        self.paths = []
        self.current_path = None
        self.name = None
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

    def clear(self):
        self.paths = []

    def save(self, basename=None):
        if not basename:
            basename = the_model.name
        with open(pathlib.Path.cwd() / (basename + '.isk'), 'wb') as f:
            pickle.dump(self.paths, f)

        # Now save an image version
        img = Image.new('RGB', self.get_size(), 'white')
        draw = ImageDraw.Draw(img)
        for path in self.paths:
            color = path.pen.color
            for line in path.lines():
                start, end = line
                draw.line([start[0], start[1], end[0], end[1]], color)

        img.save(pathlib.Path.cwd() / (basename + '.png'))

    def load(self):
        path = pathlib.Path.cwd() / (self.name + '.isk')
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.paths = pickle.load(f)

    def get_size(self):
        # TODO: Make this dynamic later to fit the image size to the actual sketch boundaries
        return 1024, 768


class Pen(object):

    def __init__(self, width=1, color=(0,0,0)):
        self.width = width
        self.color = color


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

    def points_flattened(self):
        flat_list = []
        for pt in self.points:
            flat_list.extend([pt[0], pt[1]])
        return tuple(flat_list)


the_model = SketchModel()