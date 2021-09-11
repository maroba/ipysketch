import tkinter as tk

from ipysketch.model import flatten, Pen

ICON_SIZE = 30


class ObjectVar(object):

    def __init__(self):
        self._users = []
        self._value = None

    def register_user(self, user):
        if user not in self._users:
            self._users.append(user)
            user.update()

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for user in self._users:
            user.update()


class SketchCanvas(tk.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(cursor='crosshair')

    def draw(self, model, selection=None, transform=None):

        selection = selection or []
        self.delete('all')

        for selected_path in selection:
            path = self.apply_transform(selected_path, transform)

            points = flatten(path.points)
            pen = Pen(width=path.pen.width+4, color='#00FFFF')
            if len(points) == 2:
                points = (points[0], points[1], points[0], points[1])
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width)

        for path in model.paths:

            if path in selection:
                path = self.apply_transform(path, transform)

            points = flatten(path.points)
            pen = path.pen
            if len(points) == 2:
                points = (points[0], points[1], points[0], points[1])
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width)

        lasso = model.lasso
        if lasso:
            points = flatten(lasso.points)
            pen = lasso.pen
            if len(points) == 2:
                points = (points[0], points[1], points[0], points[1])
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width, dash=pen.dash)

    def apply_transform(self, selected_path, transform):
        if transform:
            path = selected_path.clone()
            path.translate(transform.destination - transform.origin)
        else:
            path = selected_path
        return path


