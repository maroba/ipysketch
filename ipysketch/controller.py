import tkinter as tk
from tkinter import colorchooser

from ipysketch.canvas import ObjectVar, SketchCanvas
from ipysketch.buttons import ColorButton, LineWidthButton, ActionButton, LineWidthChooserDialog
from ipysketch.model import Translation, Point, filter_paths
from ipysketch.constants import *


class ButtonGroupController(object):

    def __init__(self, frame, num_buttons):
        self.parent = frame
        self.init_onoffvars(num_buttons)
        self.init_buttons(frame)

        for btn in self.buttons:
            btn.pack(side=tk.LEFT)

    def init_buttons(self):
        raise NotImplementedError

    def init_onoffvars(self, num_buttons):
        self.onoffvars = [ObjectVar() for _ in range(num_buttons)]

    def set(self, idx):
        for k, btn in enumerate(self.buttons):
            self.onoffvars[k].set(False)
        self.onoffvars[idx].set(True)

    def on_button_click(self, event):
        for k, btn in enumerate(self.buttons):
            self.onoffvars[k].set(False)
            if btn == event.widget:
                self.onoffvars[k].set(True)

    def get_selected(self):
        for i, btn in enumerate(self.buttons):
            if self.onoffvars[i].get():
                return i, btn

    def get_onoff(self, btn):
        for i, b in enumerate(self.buttons):
            if b == btn:
                return self.onoffvars[i]


class ActionButtonGroupController(ButtonGroupController):

    def __init__(self, frame):
        super().__init__(frame, 3)

    def init_buttons(self, frame):
        self.buttons = [ActionButton(frame, self.onoffvars[0], 'pen-60.png', self.on_button_click),
                        ActionButton(frame, self.onoffvars[1], 'eraser-60.png', self.on_button_click),
                        ActionButton(frame, self.onoffvars[2], 'lasso-80.png', self.on_button_click)
                        ]


class ColorButtonGroupController(ButtonGroupController):

    def __init__(self, frame):
        self.colorvars = [ObjectVar() for _ in range(3)]
        super().__init__(frame, 3)

    def init_buttons(self, frame):

        self.buttons = [ColorButton(frame, self.onoffvars[k],
                                    self.colorvars[k], self.on_button_click) for k in range(3)]

        for k, col in enumerate(('black', 'red', 'blue')):
            self.colorvars[k].set(col)

    def on_button_click(self, event):
        onoff = self.get_onoff(event.widget)
        if onoff.get():
            color = colorchooser.askcolor(title='Choose color', parent=self.parent)
            if color != (None, None):
                idx, _ = self.get_selected()
                cvar = self.colorvars[idx]
                cvar.set(color[1])

        super().on_button_click(event)

    def get(self):
        idx, _ = self.get_selected()
        return self.colorvars[idx].get()


class LineWidthButtonGroupController(ButtonGroupController):

    def __init__(self, frame, app):
        self.lwvars = [ObjectVar() for _ in range(3)]
        self.app = app
        super().__init__(frame, 3)

    def init_buttons(self, frame):

        self.buttons = [LineWidthButton(frame, self.onoffvars[k],
                                    self.lwvars[k], self.on_button_click) for k in range(3)]

        for k, lw in enumerate([2, 4, 8]):
            self.lwvars[k].set(lw)

    def on_button_click(self, event):
        onoff = self.get_onoff(event.widget)
        if onoff.get():
            lwc = LineWidthChooserDialog(self.app)

            self.app.wait_window(lwc)
            lw = lwc.get()
            if lw:
                idx, _ = self.get_selected()
                self.lwvars[idx].set(lw)

        super().on_button_click(event)

    def get(self):
        idx, _ = self.get_selected()
        return self.lwvars[idx].get()


class CanvasController(object):

    def __init__(self, app, frame):

        self.app = app

        self.canvas = SketchCanvas(frame, bd=3, background='white')
        self.canvas.grid(row=0, column=0, sticky='NWSE')

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.canvas.bind('<Button-1>', self.on_button_down)
        self.canvas.bind('<B1-Motion>', self.on_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_up)

        self.selection = []
        self.transform = None

        self.update_canvas()

    @property
    def model(self):
        return self.app.model

    def update_canvas(self):
        self.canvas.draw(self.model)

    def on_button_down(self, event):
        action = self.app.action

        at_point = Point(event.x, event.y)
        if action == ACTION_DRAW:
            self.selection = []
            self.app.trigger_dirty()
            pen = self.app.pen
            self.model.start_path(at_point, pen)
        elif action == ACTION_ERASE:
            self.selection = []
            paths_to_erase = filter_paths(self.model.paths, at_point, radius=20)
            if paths_to_erase:
                self.app.trigger_dirty()
                self.model.erase_paths(paths_to_erase)
        elif action == ACTION_LASSO:
            if self.selection:
                if filter_paths(self.selection, at_point):
                    self.start_transform(at_point)
                else:
                    self.selection = []
            else:
                self.model.start_lasso(at_point)
        else:
            raise NotImplementedError

        self.canvas.draw(self.model)

    def on_move(self, event):
        action = self.app.action
        at_point = Point(event.x, event.y)
        if action == ACTION_DRAW:
            self.model.continue_path(at_point)
        elif action == ACTION_ERASE:
            paths_to_erase = filter_paths(self.model.paths, at_point, radius=20)
            if paths_to_erase:
                self.app.trigger_dirty()
                self.model.erase_paths(paths_to_erase)
        elif action == ACTION_LASSO:
            if self.transform:
                self.continue_transform(at_point)
            elif self.model.lasso:
                self.model.continue_lasso(at_point)
        else:
            raise NotImplementedError

        self.canvas.draw(self.model, self.selection, transform=self.transform)

    def on_button_up(self, event):
        action = self.app.action
        at_point = Point(event.x, event.y)
        if action == ACTION_DRAW:
            self.model.finish_path(Point(event.x, event.y))
        elif action == ACTION_ERASE:
            paths_to_erase = filter_paths(self.model.paths, at_point, radius=20)
            if paths_to_erase:
                self.app.trigger_dirty()
                self.model.erase_paths(paths_to_erase)
        elif action == ACTION_LASSO:
            if self.transform:
                self.finish_transform(at_point)
                self.app.trigger_dirty()
            elif self.model.lasso:
                self.selection = self.model.finish_lasso(at_point)
        else:
            raise NotImplementedError

        self.canvas.draw(self.model, self.selection, self.transform)

    def start_transform(self, at_point):
        self.transform = Translation(at_point)

    def continue_transform(self, at_point):
        self.transform.destination = at_point

    def finish_transform(self, at_point):
        self.transform.destination = at_point
        for path in self.selection:
            path.translate(self.transform.destination - self.transform.origin)
        self.transform = None
