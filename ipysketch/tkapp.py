from tkinter import *
from tkinter import ttk, colorchooser
import os

import pickle
from PIL import Image, ImageTk, ImageDraw

import pkg_resources
import pathlib

from ipysketch.model import Pen, SketchModel, Circle, Point, Path, flatten

MODE_WRITE = 1
MODE_ERASE = 2
MODE_LASSO = 3


class Toolbar(Frame):
    """
    The toolbar frame.
    """

    def __init__(self, master, app):
        """ Creates the toolbar and puts it into the parent widget.

        :param master: parent frame
        :param app: the app
        """
        super().__init__(master, bd=0, relief=RAISED)
        self.parent = master

        self.app = app
        self.save_button = ToolbarButton(self, image='save-60.png', image_disabled='save-disabled-60.png')
        self.save_button.pack(side=LEFT, padx=2, pady=2)
        self.save_button.state = ToolbarButton.DISABLED

        self.pen_button = self.create_button('pen-60.png')
        self.erase_button = self.create_button('eraser-60.png')
        self.lasso_button = self.create_button('lasso-80.png')
        self.undo_button = self.create_button('undo-50.png')
        self.redo_button = self.create_button('redo-50.png')

        self.color_panel = PenColorPanel(self)
        self.color_panel.pack(side=LEFT, padx=2, pady=2)

        self.color_button = self.create_button('colors.png')
        self.color_button.pack(side=LEFT, padx=2, pady=2)

        self.line_width_panel = PenWidthPanel(self)
        self.line_width_panel.pack(side=LEFT, padx=2, pady=2)

        self.slider = LineWidthSlider(self)
        self.slider.pack(side=LEFT, padx=2)
        self.slider.bind('<ButtonRelease-1>', self.line_width_panel.set_width)

    def create_button(self, file):
        button = ToolbarButton(self, image=file)
        button.pack(side=LEFT, padx=2, pady=2)
        return button

    def save(self):
        with open(pathlib.Path.cwd() / (self.app.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.app.model, f)


class ToolbarButton(Canvas):

    NORMAL = 'normal'
    ACTIVE = 'active'
    SELECTED = 'selected'
    DISABLED = 'disabled'

    def __init__(self, master, image=None, image_selected=None, image_active=None, image_disabled=None):
        super(ToolbarButton, self).__init__(master, width=30, height=30)

        if image:
            self.image = self.create_icon(image, bg=(255, 255, 255))
        else:
            self.image = None

        if image_active:
            self.image_active = self.create_icon(image_active, bg=(255, 255, 255))
        else:
            self.image_active = self.image

        if image_selected:
            self.image_selected = self.create_icon(image_selected, bg=(255, 255, 255))
        else:
            self.image_selected = self.image

        if image_disabled:
            self.image_disabled = self.create_icon(image_disabled, bg=(255, 255, 255))
        else:
            self.image_disabled = self.image

        self.bind('<Button-1>', self._exec_command)
        self.state = ToolbarButton.NORMAL

    def create_icon(self, image, bg=(255, 255, 255)):
        img = pkg_resources.resource_filename('ipysketch', os.path.join('assets', image))
        png = Image.open(img).convert('RGBA')
        background = Image.new('RGBA', png.size, bg)
        alpha_composite = Image.alpha_composite(background, png)
        img = alpha_composite.resize((30, 30), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        return img

    def _exec_command(self, event):
        self.callback()

    def set_command(self, callback):
        self.callback = callback

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value == ToolbarButton.NORMAL:
            self.set_normal_state()
        elif value == ToolbarButton.ACTIVE:
            self.set_active_state()
        elif value == ToolbarButton.SELECTED:
            self.set_selected_state()
        elif value == ToolbarButton.DISABLED:
            self.set_disabled_state()
        else:
            raise Exception('No such state')

        self._state = value

    def set_normal_state(self):
        self.delete('all')
        self._state = ToolbarButton.NORMAL
        self.create_image(1, 1, anchor=NW, image=self.image)

    def set_active_state(self):
        pass

    def set_selected_state(self):
        self.delete('all')

        self.create_image(1, 1, anchor=NW, image=self.image_selected)
        self.create_rectangle((1, 1, 30, 30), width=1)
        self._state = ToolbarButton.SELECTED

    def set_disabled_state(self):
        self.delete('all')
        self.create_image(1, 1, anchor=NW, image=self.image_disabled)
        self._state = ToolbarButton.DISABLED

    def draw(self):
        self.label = Label(self)
        self.label.pack(side=LEFT, expand=YES, fill=BOTH)
        self.label.configure(image=self.image)

        self.create_line((0, 15, 30, 15), width=self.line_width)


class PenWidthPanel(Frame):

    def __init__(self, master, *args, **kwargs):
        super(PenWidthPanel, self).__init__(master)
        self.master = master

        self.button_1 = PenWidthButton(self, lw=2)
        self.button_1.bind('<Button-1>', self.handle)
        self.button_1.pack(side=LEFT, padx=2, pady=2)
        self.button_2 = PenWidthButton(self, lw=4)
        self.button_2.bind('<Button-1>', self.handle)
        self.button_2.pack(side=LEFT, padx=2, pady=2)
        self.button_3 = PenWidthButton(self, lw=8)
        self.button_3.bind('<Button-1>', self.handle)
        self.button_3.pack(side=LEFT, padx=2, pady=2)

        self.button_1.state = ToolbarButton.SELECTED
        self._selected_btn = self.button_1

    @property
    def selected_button(self):
        return self._selected_btn

    def handle(self, event):
        if event.widget != self._selected_btn:
            self._selected_btn.state = ToolbarButton.NORMAL
            self._selected_btn = event.widget
            self._selected_btn.state = ToolbarButton.SELECTED
            self.master.slider.set(self._selected_btn.line_width)

    def set_width(self, event):
        lw = event.widget.get()
        self.selected_button.set_width(lw)


class PenWidthButton(ToolbarButton):

    def __init__(self, master, lw):
        self.line_width = lw
        self.master = master
        super(PenWidthButton, self).__init__(master)
        self.state = ToolbarButton.NORMAL

    def set_width(self, lw):
        self.line_width = lw
        self.state = self.state

    def set_selected_state(self):
        self.delete('all')
        self.create_rectangle((1, 1, 30, 30), width=1)
        self.create_line((0, 15, 30, 15), width=self.line_width)

    def set_normal_state(self):
        self.delete('all')
        self.create_line((0, 15, 30, 15), width=self.line_width)


class PenColorPanel(Frame):

    def __init__(self, master):
        super(PenColorPanel, self).__init__(master)

        self.button_1 = PenColorButton(self, '#000000')
        self.button_1.bind('<Button-1>', self.handle)
        self.button_1.pack(side=LEFT, padx=2, pady=2)

        self.button_2 = PenColorButton(self, '#FF0000')
        self.button_2.bind('<Button-1>', self.handle)
        self.button_2.pack(side=LEFT, padx=2, pady=2)

        self.button_3 = PenColorButton(self, '#0000FF')
        self.button_3.bind('<Button-1>', self.handle)
        self.button_3.pack(side=LEFT, padx=2, pady=2)

        self.button_1.state = ToolbarButton.SELECTED
        self._selected_button = self.button_1

    @property
    def selected_button(self):
        return self._selected_button

    def handle(self, event):
        self._selected_button.state = ToolbarButton.NORMAL
        self._selected_button = event.widget
        self._selected_button.state = ToolbarButton.SELECTED


class PenColorButton(ToolbarButton):

    def __init__(self, master, color):
        self.color = color
        super(PenColorButton, self).__init__(master)
        self.state = ToolbarButton.NORMAL

    def set_selected_state(self):
        self.delete('all')
        self.create_rectangle((1, 1, 30, 30), width=1)
        self.create_oval((8, 8, 22, 22), fill=self.color)

    def set_normal_state(self):
        self.delete('all')
        self.create_oval((8, 8, 22, 22), fill=self.color)

    def set_color(self, color):
        self.color = color
        self.state = self.state


class Sketchpad(Canvas):

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, background='white', cursor='cross', **kwargs)

        self.app = app
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.bind('<B1-Motion>', self.on_move)

        self.current_pen = None
        self.color = (0, 0, 0), '#000000'

        self._lasso_path = None
        self.selected_paths_uuids = []

    def on_button_down(self, event):
        if not self.contains(event):
            return

        self.current_action = {}

        if self.app.mode == MODE_WRITE:
            self.app.trigger_action_begins()
            self.current_action['type'] = 'write'
            self.app.model.start_path(event.x, event.y, self.app.get_current_pen())
        elif self.app.mode == MODE_ERASE:
            self.app.trigger_action_begins()
            self.current_action['type'] = 'erase'
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()
        elif self.app.mode == MODE_LASSO:

            if self.selected_paths_uuids:

                for path in self.app.model.filter_by_uuids(self.selected_paths_uuids):
                    circle = Circle((event.x, event.y), 20)
                    if path.overlaps(circle):
                        self.current_action['type'] = 'transform'
                        self.current_action['start_point'] = Point((event.x, event.y))
                if 'type' not in self.current_action:
                    self.current_action['type'] = 'select'
                    self.selected_paths_uuids = []
                    self.draw_all()
            else:
                self.current_action['type'] = 'select'

            if self.current_action['type'] == 'select':
                self._lasso_path = Path()
                self._lasso_path.pen.dash = (3, 5)
                self._lasso_path.add_point(event.x, event.y)
            else:
                self.app.trigger_action_begins()

    def delete_paths_at(self, x, y, radius):
        paths_to_delete = self.app.model.find_paths(x, y, radius=radius)
        for p in paths_to_delete:
            self.app.model.remove(p)
        return len(paths_to_delete) > 0

    def on_button_up(self, event):
        if self.app.mode == MODE_WRITE:
            pass # nothing to do any more
        elif self.app.mode == MODE_LASSO:
            if self.current_action['type'] == 'select':
                paths = []
                for path in self.app.model.paths:
                    for pt in path.points:
                        if self._lasso_path.contains(pt):
                            paths.append(path.uuid)
                            break
                self.selected_paths_uuids = paths

                self._lasso_path = None
                self.draw_all()
            elif self.current_action['type'] == 'transform':
                for path in self.app.model.paths:
                    path.apply_offset()

        self.current_action = None

    def on_move(self, event):

        if not self.contains(event):
            return

        if not self.current_action:
            return

        if self.app.mode == MODE_WRITE:
            self.app.model.add_to_path(event.x, event.y)
            self._add_line()

        elif self.app.mode == MODE_ERASE:
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()
        elif self.app.mode == MODE_LASSO:
            if self.current_action['type'] == 'select':
                if self._lasso_path is not None:
                    self._lasso_path.add_point(event.x, event.y)
                    self.draw_line((self._lasso_path.points[-2], self._lasso_path.points[-1]),
                                   self._lasso_path.pen,
                                   dash=self._lasso_path.pen.dash)
                    return
            elif self.current_action['type'] == 'transform':
                offset = Point((event.x, event.y)) - self.current_action['start_point']
                for path in self.app.model.paths:
                    if path.uuid in self.selected_paths_uuids:
                        path.offset = offset
                self.draw_all()

    def _add_line(self):
        path = self.app.get_current_path()
        p_from, p_to = path.points[-2], path.points[-1]
        self.draw_line((p_from.x, p_from.y, p_to.x, p_to.y), path.pen)

    def contains(self, event):
        w, h = self.get_size()
        bd = 5
        return bd < event.x < w - bd and bd < event.y < h - bd

    def get_size(self):
        return self.winfo_width(), self.winfo_height()

    def draw_all(self):
        self.delete('all')

        for path in self.app.model.paths:
            if path.uuid in self.selected_paths_uuids:
                pts = path.points_flattened()
                self.draw_line(pts, path.pen, color='#00FFFF', width=path.pen.width + 4, dash=(3, 5))

            pts = path.points_flattened()
            self.draw_line(pts, pen=path.pen)

        if self._lasso_path:
            self.draw_line(self._lasso_path.points, self._lasso_path.pen)

    def draw_line(self, points, pen, **kwargs):

        cfg = {
            'width': kwargs.get('width', pen.width),
            'fill': kwargs.get('color', pen.color),
            'dash': kwargs.get('dash', pen.dash),
            'capstyle': ROUND,
            'smooth': 1,
            'splinesteps': 12
        }

        if not points:
            return

        if isinstance(points[0], Point):
            points = flatten(points)

        if len(points) < 4:
            return

        self.create_line(points, cfg)


class LineWidthSlider(Canvas):

    def __init__(self, master):
        self.width = 120
        self.lw = 2
        super(LineWidthSlider, self).__init__(master, height=32, width=self.width)
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<B1-Motion>', self.on_move)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.callback = None # when value changed
        self.draw()

    def on_button_down(self, event):
        self.set(int(event.x / self.width * 30) + 1)
        self.draw()

    def on_move(self, event):
        self.set(int(event.x / self.width * 30) + 1)
        self.draw()

    def on_button_up(self, event):
        self.set(int(event.x / self.width * 30) + 1)
        self.draw()
        self.callback()

    def set(self, value):
        self.lw = value
        if self.lw > 30:
            self.lw = 30
        if self.lw < 1:
            self.lw = 1
        self.draw()

    def get(self):
        return self.lw

    def draw(self):
        self.delete('all')
        posx = int((self.lw-1) / 30 * self.width)+2
        self.create_polygon((0, 14, self.width, 30, self.width, 2), fill='#000000')
        self.create_rectangle((posx, 28, posx+4, 0), fill='#888888')


class SketchApp(object):

    def __init__(self, name):

        self.history = [SketchModel(name)]
        self._model_ptr = 0

        root = Tk()
        root.title('ipysketch: ' + name)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.geometry('1024x768+200+200')

        toolbar = Toolbar(root, self)
        toolbar.grid(column=0, row=0, sticky=(N, W, E, S))

        pad = Sketchpad(root, self)
        pad.grid(column=0, row=1, sticky=(N, W, E, S), padx=(5, 5), pady=(5, 5))

        self.root = root
        self.toolbar = toolbar
        self.pad = pad

        self.toolbar.save_button.set_command(self.save)
        self.toolbar.pen_button.set_command(self.set_write_mode)

        self.toolbar.erase_button.set_command(self.set_erase_mode)
        self.toolbar.lasso_button.set_command(self.set_lasso_mode)
        self.toolbar.color_button.set_command(self.choose_color)
        self.toolbar.undo_button.set_command(self.undo_action)
        self.toolbar.redo_button.set_command(self.redo_action)

        # Load drawing, if available
        isk_file = pathlib.Path.cwd() / str(name + '.isk')
        if os.path.exists(isk_file):
            with open(isk_file, 'rb') as f:
                self.model = pickle.load(f)
            self.pad.draw_all()

        self.toolbar.slider.callback = self.set_line_width
        self.start_mode(MODE_WRITE)
        self.root.attributes('-topmost', True)

    def get_current_line_width(self):
        return self.toolbar.line_width_panel.selected_button.line_width

    def get_current_color(self):
        return self.toolbar.color_panel.selected_button.color

    def get_current_path(self):
        return self.model.paths[-1]

    def get_current_pen(self):
        pen = Pen()
        pen.color = self.toolbar.color_panel.selected_button.color
        pen.width = self.toolbar.line_width_panel.selected_button.line_width
        return pen

    def set_line_width(self):
        lw = self.toolbar.slider.get()
        self.toolbar.line_width_panel.selected_button.set_width(lw)

    @property
    def model(self):
        return self.history[self._model_ptr]

    @model.setter
    def model(self, value):
        self.history[self._model_ptr] = value

    def run(self):
        self.root.mainloop()

    def save(self):

        if not self.model.dirty:
            return

        with open(pathlib.Path.cwd() / (self.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.model, f)

        self.export_to_png()

        self.model.dirty = False
        self.toolbar.save_button.state = ToolbarButton.DISABLED

    def export_to_png(self):
        ul, lr = self.model.get_bounding_box()

        width = lr.x - ul.x
        height = lr.y - ul.y
        width += 4
        height += 4

        maxw = 0
        for p in self.model.paths:
            if p.pen.width / 2 > maxw:
                maxw = p.pen.width // 2

        width += 2 * maxw
        height += 2 * maxw

        if width < 0 or height < 0:
            return

        offset = ul - Point((maxw+ 2, maxw + 2))
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        for path in self.model.paths:
            color = path.pen.color
            width = path.pen.width
            radius = width // 2 - 2

            points = path.smoothed_points()

            for i in range(1, len(points)):
                start = points[i-1] - offset
                end = points[i] - offset

                if width > 2:
                    circle = Circle(start, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)
                    circle = Circle(end, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)

                draw.line([round(start.x), round(start.y),
                           round(end.x), round(end.y)], fill=color, width=width)

        img.save(pathlib.Path.cwd() / (self.model.name + '.png'))

    def set_write_mode(self):
        self.end_mode()
        self.start_mode(MODE_WRITE)

    def set_erase_mode(self):
        self.end_mode()
        self.start_mode(MODE_ERASE)

    def set_lasso_mode(self):
        self.end_mode()
        self.start_mode(MODE_LASSO)

    def end_mode(self):
        if self.mode == MODE_LASSO:
            self.pad.selected_paths_uuids = []
            self.pad.draw_all()
            self.toolbar.lasso_button.state = ToolbarButton.NORMAL
        elif self.mode == MODE_WRITE:
            self.toolbar.pen_button.state = ToolbarButton.NORMAL
        elif self.mode == MODE_ERASE:
            self.toolbar.erase_button.state = ToolbarButton.NORMAL
        else:
            raise Exception('No such state')

    def start_mode(self, mode):
        self.mode = mode
        if self.mode == MODE_LASSO:
            self.toolbar.lasso_button.state = ToolbarButton.SELECTED
        elif self.mode == MODE_WRITE:
            self.toolbar.pen_button.state = ToolbarButton.SELECTED
        elif self.mode == MODE_ERASE:
            self.toolbar.erase_button.state = ToolbarButton.SELECTED
        else:
            raise Exception('No such state')

    def choose_color(self):
        self.root.attributes('-topmost', False)
        color = colorchooser.askcolor(title='Choose color')
        if color != (None, None):
            self.toolbar.color_panel.selected_button.set_color(color[1])

    def trigger_action_begins(self):
        if self._model_ptr < len(self.history) - 1:
            self.history = self.history[:self._model_ptr+1]
        self.history.append(self.model.clone())
        self._model_ptr += 1
        self.model.dirty = True
        self.toolbar.save_button.state = ToolbarButton.NORMAL

    def undo_action(self):
        if self._model_ptr > 0:
            self._model_ptr -= 1
            self.pad.draw_all()

    def redo_action(self):
        if self._model_ptr < len(self.history) - 1:
            self._model_ptr += 1
            self.pad.draw_all()


def main(name):
    SketchApp(name).run()
