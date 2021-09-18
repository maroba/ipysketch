import tkinter as tk

from ipysketch.model import flatten, Pen, Point

ICON_SIZE = 30


class ObjectVar(object):
    """
    Generalization of the tkinter classes StringVar, IntVar, etc. for general objects.
    """

    def __init__(self):
        self._users = []
        self._value = None

    def register(self, user):
        """Register an observer that is notified whenever the value changes.
           Observers must implement the update() function.
        """
        if user not in self._users:
            self._users.append(user)
            user.update()

    def get(self):
        """Get the current value."""
        return self._value

    def set(self, value):
        """Set the current value."""
        self._value = value
        for user in self._users:
            user.update()


class SketchCanvas(tk.Canvas):
    """ Customization of the standard TK Canvas class """

    def __init__(self, *args, **kwargs):
        self._scroll_region = (-1500, -1500, 1500, 1500)
        super().__init__(*args, scrollregion=self._scroll_region, **kwargs)
        self.config(cursor='crosshair')

    def update_paths(self, *paths, transform=None, selected=False):
        """ Update one or more paths on the canvas.

        :param paths: List or variable arg list of Path objects
        :param transform: transformation to apply to paths
        :param selected: paint as selected paths or not
        :return:
        """

        if isinstance(paths[0], list):
            paths = paths[0]

        for path in paths:
            if transform:
                path = self.apply_transform(path, transform)
            self.delete(path.uuid)
            points = flatten(path.points)
            if selected:
                pen = Pen(width=path.pen.width + 4, color='#00FFFF')
                if len(points) == 2:
                    points = (points[0], points[1], points[0], points[1])
                self.create_line(points, fill=pen.color, smooth=True, width=pen.width, tag=path.uuid)

            self.create_line(points, fill=path.pen.color, smooth=True, width=path.pen.width, tag=path.uuid)

    def delete_paths(self, *paths):
        """ Delete one or more paths from the canvas.

        :param paths: list or variable arg list of Path objects to remove
        :return:
        """
        if isinstance(paths[0], list):
            paths = paths[0]
        for p in paths:
            self.delete(p.uuid)

    def draw(self, model, selection=None, transform=None):
        """ Redraw the complete model.

        :param model: the model instance
        :param selection: the list of paths that shall be drawn as selected
        :param transform: the transformation to apply to the selection
        :return:
        """

        selection = selection or []
        self.delete('all')

        for selected_path in selection:
            path = self.apply_transform(selected_path, transform)
            points = flatten(path.points)
            pen = Pen(width=path.pen.width+4, color='#00FFFF')
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width, tag=path.uuid)

        for path in model.paths:
            if path in selection:
                path = self.apply_transform(path, transform)
            points = flatten(path.points)
            pen = path.pen
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width, tag=path.uuid)

        lasso = model.lasso
        if lasso:
            points = flatten(lasso.points)
            pen = lasso.pen
            if len(points) == 2:
                points = (points[0], points[1], points[0], points[1])
            self.create_line(points, fill=pen.color, smooth=True, width=pen.width, dash=pen.dash, tag=path.uuid)

    def apply_transform(self, selected_path, transform):
        """ Apply a transformation to the given path.

        :param selected_path: Path object
        :param transform: Transformation object
        :return:
        """
        if transform:
            path = selected_path.clone()
            path.translate(transform.destination - transform.origin)
        else:
            path = selected_path
        return path

    def shift(self, translation):
        """ Shift the visible part of the canvas

        :param translation: direction and size of the shift; Translation object
        :return:
        """
        W = self._scroll_region[2] - self._scroll_region[0]
        H = self._scroll_region[3] - self._scroll_region[1]
        xv , yv = self.xview(), self.yview()

        delta = translation.destination - translation.origin

        dxv0 = -delta.x / W
        dyv0 = -delta.y / H

        xv_new_0 = xv[0] + dxv0
        yv_new_0 = yv[0] + dyv0

        self.xview_moveto(xv_new_0)
        self.yview_moveto(yv_new_0)
        translation.origin = translation.destination
        translation.destination = None

    def origin(self):
        """ Returns the origin of the window in canvas coordinates """
        return Point(self.canvasx(0), self.canvasy(0))