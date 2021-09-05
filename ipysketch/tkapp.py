from tkinter import *
from tkinter import ttk, colorchooser
import os
import re
import sys

import pickle
from PIL import Image, ImageTk, ImageDraw
from tkinter import Tk, Frame, Button

from tkinter import LEFT, TOP, X, FLAT, RAISED

import pkg_resources
import pathlib

from ipysketch.model import Pen, SketchModel, Circle, Point, Vector

MODE_WRITE = 1
MODE_ERASE = 2


class Toolbar(Frame):

    def __init__(self, master, app):
        super().__init__(master, bd=1, relief=RAISED)
        self.parent = master

        self.app = app
        self.save_button = self.create_button('save-60.png')
        self.pen_button = self.create_button('pen-60.png')
        self.erase_button = self.create_button('eraser-60.png')
        self.undo_button = self.create_button('undo-50.png')
        self.redo_button = self.create_button('redo-50.png')

        self.line_width = DoubleVar()
        self.width_scale = Scale(self, variable=self.line_width, from_=1, to=100, orient=HORIZONTAL, label='Line width')
        self.width_scale.pack(side=LEFT, padx=2, pady=2)

        def check_color(newval):
            return re.match('^#[0-9A-Fa-f]*$', newval) is not None and len(newval) <= 7
        check_color_wrapper = (master.register(check_color), '%P')

        self.color_button = Button(self, text='Color')
        self.color_button.pack(side=LEFT, padx=2, pady=2)

        #self.color_string = StringVar(value='#000000')
        #self.color_entry = Entry(self, textvariable=self.color_string, validate='key', validatecommand=check_color_wrapper)
        #self.color_entry.pack(side=LEFT, padx=2, pady=2)

    def create_button(self, file):

        img = pkg_resources.resource_filename('ipysketch', 'assets/' + file)
        img = Image.open(img)
        img = img.resize((30, 30))
        img = ImageTk.PhotoImage(img)

        #style = ttk.Style()
        #style.map(
        #    "Custom.TButton",
        #    image=[
        #        ("disabled", img),
        #        ("!disabled", img),
        #        ("active", img)
        #    ]
        #)

        #button = ttk.Button(self, style=style)
        button = Button(self, image=img, relief=FLAT)
        button.image = img
        button.pack(side=LEFT, padx=2, pady=2)
        return button

    def save(self):
        with open(pathlib.Path.cwd() / (self.app.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.app.model, f)


class Sketchpad(Canvas):

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, background='white', cursor='cross', **kwargs)

        self.app = app
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<ButtonRelease-1>', self.on_button_up)
        self.bind('<B1-Motion>', self.on_move)

        self.current_pen = None
        self.color = (0, 0, 0), '#000000'

    def on_button_down(self, event):
        if not self.contains(event):
            return

        self.app.trigger_action_begins()

        if self.app.mode == MODE_WRITE:
            self.current_pen = Pen(width=self.app.toolbar.width_scale.get(),
                                   color=self.color[1])
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
            self._add_line(event, self.current_pen.color, self.current_pen.width)
            self.app.model.add_to_path(event.x, event.y)
            if not self.contains(event):
                return
        else:
            if self.delete_paths_at(event.x, event.y, radius=10):
                self.draw_all()

    def _save_posn(self, event):
        self.lastx, self.lasty = event.x, event.y

    def _add_line(self, event, color, width):
        if not self.contains(event):
            return
        #self.create_line((self.lastx, self.lasty, event.x, event.y), fill=color, width=width, joinstyle=ROUND)
        self.draw_line((self.lastx, self.lasty), (event.x, event.y), self.current_pen)
        self._save_posn(event)

    def contains(self, event):
        w, h = self.get_size()
        bd = 5
        return bd < event.x < w - bd and bd < event.y < h - bd

    def get_size(self):
        return self.winfo_width(), self.winfo_height()

    def draw_all(self):
        self.delete('all')
        for path in self.app.model.paths:
            for line in path.lines_flat():
                self.draw_line((line[0], line[1]), (line[2], line[3]), path.pen)

    def draw_line(self, start, end, pen):
        self.create_line((start[0], start[1], end[0], end[1]), width=pen.width,
                         capstyle=ROUND, fill=pen.color)



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

        self.toolbar.save_button.bind('<Button-1>', self.save)
        self.toolbar.pen_button.bind('<Button-1>', self.set_write_mode)
        self.toolbar.erase_button.bind('<Button-1>', self.set_erase_mode)
        self.toolbar.color_button.bind('<Button-1>', self.choose_color)
        self.toolbar.undo_button.bind('<Button-1>', self.undo_action)
        self.toolbar.redo_button.bind('<Button-1>', self.redo_action)

        # Load drawing, if available
        isk_file = pathlib.Path.cwd() / str(name + '.isk')
        if os.path.exists(isk_file):
            with open(isk_file, 'rb') as f:
                self.model = pickle.load(f)
            self.pad.draw_all()

        self.mode = MODE_WRITE
        self.root.attributes('-topmost', True)

    @property
    def model(self):
        return self.history[self._model_ptr]

    @model.setter
    def model(self, value):
        self.history[self._model_ptr] = value

    def run(self):
        self.root.mainloop()

    def save(self, event):

        with open(pathlib.Path.cwd() / (self.model.name + '.isk'), 'wb') as f:
            pickle.dump(self.model, f)

        self.export_to_png()

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
            radius = width // 2
            for line in path.lines():
                start, end = line
                start = start - offset
                end = end - offset

                if width > 2:
                    circle = Circle(start, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)
                    circle = Circle(end, radius)
                    cul = circle.upper_left()
                    clr = circle.lower_right()
                    draw.ellipse((cul.x, cul.y, clr.x, clr.y), fill=color)

                draw.line([int(start.x), int(start.y),
                           int(end.x), int(end.y)], fill=color, width=width)

        img.save(pathlib.Path.cwd() / (self.model.name + '.png'))

    def set_write_mode(self, event):
        self.mode = MODE_WRITE

    def set_erase_mode(self, event):
        self.mode = MODE_ERASE

    def choose_color(self, event):
        self.root.attributes('-topmost', False)
        self.pad.color = colorchooser.askcolor(title='Choose color')

    def trigger_action_begins(self):
        if self._model_ptr < len(self.history) - 1:
            self.history = self.history[:self._model_ptr+1]
        self.history.append(self.model.clone())
        self._model_ptr += 1

    def undo_action(self, event):
        if self._model_ptr > 0:
            self._model_ptr -= 1
            self.pad.draw_all()

    def redo_action(self, event):
        if self._model_ptr < len(self.history) - 1:
            self._model_ptr += 1
            self.pad.draw_all()


def main(name):
    SketchApp(name).run()
