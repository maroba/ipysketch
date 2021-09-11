import tkinter as tk

import pickle
import os
import io
from PIL import Image

from ipysketch.controller import ColorButtonGroupController, ActionButtonGroupController, \
    CanvasController, LineWidthButtonGroupController
from ipysketch.canvas import ObjectVar
from ipysketch.buttons import SimpleIconButton, SaveButton
from ipysketch.constants import *
from ipysketch.model import Pen, SketchModel, History


class Application(tk.Tk):

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = name

        self.history = self.create_model_history()

        self.create_toolbar()
        self.create_canvas()
        self.configure_window()

    def configure_window(self):
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.geometry('800x600+100+100')
        self.lift()
        self.attributes('-topmost', True)

    def create_canvas(self):
        frame = tk.Frame(self, border=4)
        frame.grid(row=1, column=0, sticky='NWSE')
        self.canvas_controller = CanvasController(self, frame)

    def create_toolbar(self):
        frame = tk.Frame(self, border=3)
        frame.grid(row=0, column=0, sticky='WE')
        self.dirty = ObjectVar()
        self.dirty.set(False)
        SaveButton(frame, self.dirty, self.save).pack(side=tk.LEFT)
        self.action_controller = ActionButtonGroupController(frame)
        self.action_controller.onoffvars[0].set(True)
        self.undo_var = ObjectVar()
        self.undo_var.set('normal')
        self.redo_var = ObjectVar()
        self.redo_var.set('normal')
        SimpleIconButton(frame, {'normal': 'undo-50.png'}, self.undo_var, self.undo).pack(side=tk.LEFT)
        SimpleIconButton(frame, {'normal': 'redo-50.png'}, self.redo_var, self.redo).pack(side=tk.LEFT)
        self.colors_controller = ColorButtonGroupController(frame)
        self.colors_controller.onoffvars[0].set(True)
        self.linewidth_controller = LineWidthButtonGroupController(frame, self)
        self.linewidth_controller.onoffvars[0].set(True)

    def create_model_history(self):
        file_name = self.name + '.isk'
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                model = pickle.load(f)
        else:
            model = SketchModel()

        return History(model)

    @property
    def model(self):
        return self.history.current()

    @property
    def action(self):
        selected = self.action_controller.get_selected()[0]
        if selected == 0:
            return ACTION_DRAW
        elif selected == 1:
            return ACTION_ERASE
        elif selected == 2:
            return ACTION_LASSO
        else:
            raise Exception('No such mode')

    @action.setter
    def action(self, value):
        if value == ACTION_DRAW:
            self.action_controller.set(0)
        elif value == ACTION_ERASE:
            self.action_controller.set(1)
        elif value == ACTION_LASSO:
            self.action_controller.set(2)

    @property
    def pen(self):
        color = self.colors_controller.get()
        width = self.linewidth_controller.get()
        return Pen(color=color, width=width)

    def save(self, event):

        with open(os.path.join(os.curdir, self.name + '.isk'), 'wb') as f:
            pickle.dump(self.canvas_controller.model, f)

        png_name = os.path.join(os.curdir, self.name + '.png')
        if len(self.model.paths) == 0:
            if os.path.exists(png_name):
                os.remove(png_name)
            self.dirty.set(False)
            return

        bbox = self.model.bbox()
        w = bbox.lr.x - bbox.ul.x
        h = bbox.lr.y - bbox.ul.y
        ps = self.canvas_controller.canvas.postscript(colormode='color', x=bbox.ul.x-20, y=bbox.ul.y-20, width=w+40, height=h+40)
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save(png_name)

        self.dirty.set(False)

    def undo(self, event):
        self.history.back()
        self.canvas_controller.update_canvas()

    def redo(self, event):
        self.history.forward()
        self.canvas_controller.update_canvas()

    def trigger_dirty(self):
        self.history.new()
        self.dirty.set(True)


def main(name):
    app = Application(name)
    app.wait_visibility()
    app.attributes('-topmost', False)

    app.mainloop()

