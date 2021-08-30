import os
import pathlib
import pickle


class SketchModel(object):

    def __init__(self):
        self.paths = []

    def add_path(self, path):
        self.paths.append(path)

    def clear(self):
        self.paths = []

    def save(self, basename):
        with open(pathlib.Path.cwd() / (basename + '.isk'), 'wb') as f:
            pickle.dump(self.paths, f)

    def load(self, file_name):
        if not file_name.endswith('.isk'):
            file_name += '.isk'
        path = pathlib.Path.cwd() / file_name
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.paths = pickle.load(f)


class Path(object):

    def __init__(self, line_width):
        self.line_width = line_width
        self.points = []

    def add_point(self, x, y):
        self.points.append((x, y))

    def points_flattened(self):
        flat_list = []
        for pt in self.points:
            flat_list.extend([pt[0], pt[1]])
        return tuple(flat_list)