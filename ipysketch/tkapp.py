from tkinter import *
from tkinter import ttk
import os

import pickle
from PIL import Image, ImageTk, ImageDraw
from tkinter import Tk, Frame, Button, Widget
from tkinter import LEFT, TOP, X, FLAT, RAISED

import pkg_resources
import pathlib

from ipysketch.model import Pen, SketchModel

MODE_WRITE = 1
MODE_ERASE = 2


class Toolbar(Frame):

    def __init__(self, master, app):
        super().__init__(master, bd=1, relief=RAISED)

        self.app = app
        self.save_button = self.create_button('save-60.png', self.save)
        self.pen_button = self.create_button('pen-60.png', self.write)
        self.erase_button = self.create_button('eraser-60.png', self.write)

    def create_button(self, file, callback):

        img = pkg_resources.resource_filename('ipysketch', 'assets/' + file)
        img = Image.open(img)
        img = ImageTk.PhotoImage(img)

        button = Button(self, image=img, relief=FLAT, command=callback)
        button.image = img
        button.pack(side=LEFT, padx=2, pady=2)
        return button

    def save(self):
        with open(pathlib.Path.cwd() / (self.app.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.app.model, f)

    def write(self):
        pass


class Sketchpad(Canvas):

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, background='white', **kwargs)

        self.app = app
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.bind('<B1-Motion>', self.on_move)

        self.current_pen = Pen()

        self.map_canvas_ids_to_model = {}

    def on_button_down(self, event):
        if not self.contains(event):
            return
        if self.app.mode == MODE_WRITE:
            self.app.model.start_path(event.x, event.y, self.current_pen)
            self._save_posn(event)
        else:
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()

    def delete_paths_at(self, x, y, radius):
        paths_to_delete = self.app.model.find_paths(x, y, radius=radius)
        for p in paths_to_delete:
            self.app.model.remove(p)
        return len(paths_to_delete) > 0

    def on_button_up(self, event):
        self.app.model.finish_path()

    def on_move(self, event):
        if self.app.mode == MODE_WRITE:
            self._add_line(event)
            self.app.model.add_to_path(event.x, event.y)
            if not self.contains(event):
                return
        else:
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()

    def _save_posn(self, event):
        self.lastx, self.lasty = event.x, event.y

    def _add_line(self, event):
        if not self.contains(event):
            return
        canvas_id = self.create_line((self.lastx, self.lasty, event.x, event.y))
        self._save_posn(event)

    def contains(self, event):
        w, h = self.get_size()
        bd = 5
        return event.x > bd and event.y > bd and event.x < w-bd and event.y < h-bd

    def get_size(self):
        return self.winfo_width(), self.winfo_height()

    def draw_all(self):
        self.delete('all')
        for path in self.app.model.paths:
            for line in path.lines_flat():
                self.create_line(line, fill=path.pen.color)


class SketchApp(object):

    def __init__(self, name):

        self.model = SketchModel(name)

        root = Tk()

        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.geometry('1024x768+200+200')
        root.attributes('-topmost', True)

        toolbar = Toolbar(root, self)
        toolbar.grid(column=0, row=0, sticky=(N, W, E, S))

        pad = Sketchpad(root, self)
        pad.grid(column=0, row=1, sticky=(N, W, E, S), padx=(5, 5), pady=(5, 5))

        self.root = root
        self.toolbar = toolbar
        self.pad = pad

        self.toolbar.save_button.bind('<Button-1>', self.save)
        self.toolbar.pen_button.bind('<Button-1>', self.set_write_mode)
        self.toolbar.erase_button.bind('<Button-1>', self.set_erase_mode)

        # Load drawing, if available
        isk_file = pathlib.Path.cwd() / str(name + '.isk')
        if os.path.exists(isk_file):
            with open(isk_file, 'rb') as f:
                self.model = pickle.load(f)
            self.pad.draw_all()

        self.mode = MODE_WRITE

    def run(self):
        self.root.mainloop()

    def save(self, event):

        with open(pathlib.Path.cwd() / (self.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.model, f)

        self.export_to_png()

    def export_to_png(self):

        bb = self.model.get_bounding_box()
        width = bb[1][0] - bb[0][0]
        height = bb[1][1] - bb[0][1]
        offset = bb[0]
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        for path in self.model.paths:
            color = path.pen.color
            for line in path.lines():
                start, end = line
                draw.line([int(start[0] - offset[0]), int(start[1] - offset[1]),
                           int(end[0] - offset[0]), int(end[1] - offset[1])], color)

        img.save(pathlib.Path.cwd() / (self.model.name + '.png'))


    def set_write_mode(self, event):
        self.mode = MODE_WRITE

    def set_erase_mode(self, event):
        self.mode = MODE_ERASE


def main(name):
    SketchApp(name).run()
