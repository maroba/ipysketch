from tkinter import *
from tkinter import ttk
import os

import pickle
from PIL import Image, ImageTk
from tkinter import Tk, Frame, Button, Widget
from tkinter import LEFT, TOP, X, FLAT, RAISED

import pkg_resources
import pathlib

from ipysketch.model import Pen, the_model

MODE_WRITE = 1


class Toolbar(Frame):

    def __init__(self, master):
        super().__init__(master, bd=1, relief=RAISED)

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
        with open(pathlib.Path.cwd() / (the_model.name + '.isk'), 'wb') as f:
            pickle.dump(the_model, f)

    def write(self):
        pass


class Sketchpad(Canvas):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, background='white', **kwargs)
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.bind('<B1-Motion>', self.on_move)

        self.current_pen = Pen()

        self.map_canvas_ids_to_model = {}

    def on_button_down(self, event):
        if not self.contains(event):
            return
        the_model.start_path(event.x, event.y, self.current_pen)
        self._save_posn(event)

    def on_button_up(self, event):
        the_model.finish_path()

    def on_move(self, event):
        self._add_line(event)
        the_model.add_to_path(event.x, event.y)
        if not self.contains(event):
            return

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
        for path in the_model.paths:
            for line in path.lines_flat():
                self.create_line(line, fill=path.pen.color)


class SketchApp(object):

    def __init__(self, name):
        the_model.name = name
        root = Tk()

        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.geometry('1024x768+200+200')
        root.attributes('-topmost', True)

        toolbar = Toolbar(root)
        toolbar.grid(column=0, row=0, sticky=(N, W, E, S))

        pad = Sketchpad(root)
        pad.grid(column=0, row=1, sticky=(N, W, E, S), padx=(5, 5), pady=(5, 5))

        self.root = root
        self.toolbar = toolbar
        self.pad = pad

        self.toolbar.save_button.bind('<Button-1>', self.save)
        self.toolbar.pen_button.bind('<Button-1>', self.set_write_mode)
        self.toolbar.erase_button.bind('<Button-1>', self.set_erase_mode)

        # Load drawing, if available
        if os.path.exists(pathlib.Path.cwd() / str(name + '.isk')):
            the_model.load()
            self.pad.draw_all()

    def run(self):
        self.root.mainloop()

    def save(self, event):
        the_model.save()

    def set_write_mode(self, event):
        pass

    def set_erase_mode(self, event):
        pass


def main(name):
    SketchApp(name).run()
