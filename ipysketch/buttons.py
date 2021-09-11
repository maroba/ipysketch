import os
import tkinter as tk
from tkinter import ttk
from tkinter.commondialog import Dialog

import pkg_resources
from PIL import Image, ImageTk

from ipysketch.canvas import ICON_SIZE


class ToolbarButton(tk.Canvas):

    def __init__(self, parent, variable, callback, *args, **kwargs):
        self.variable = variable
        self.callback = callback
        super(ToolbarButton, self).__init__(parent, width=ICON_SIZE, height=ICON_SIZE, *args, **kwargs)
        self.bind('<Button-1>', callback)
        self.variable.register_user(self)

    def update(self):
        self.draw()

    def draw(self):
        self.delete('all')
        self.draw_interior()

    def draw_interior(self):
        raise NotImplementedError


class SelectableButton(ToolbarButton):

    def __init__(self, parent, onoff, callback=None, *args, **kwargs):
        self.onoff = onoff
        super().__init__(parent, onoff, callback)
        self.draw()

    def update(self):
        self.draw()

    def draw(self):
        super().draw()
        self.draw_outline()

    def draw_outline(self):
        if self.onoff.get():
            self.create_rectangle((0, 0, ICON_SIZE, ICON_SIZE), outline='black')


class ColorButton(SelectableButton):

    def __init__(self, parent, onoff, color, callback=None, *args, **kwargs):
        self.color = color
        super().__init__(parent, onoff, callback, *args, **kwargs)
        self.color.register_user(self)

    def draw_interior(self):
        self.create_rectangle((1, 1, ICON_SIZE, ICON_SIZE), fill='#FFFFFF', outline='#FFFFFF')
        self.create_oval((5, 5, ICON_SIZE - 2, ICON_SIZE - 2), fill=self.color.get())


class LineWidthButton(SelectableButton):

    def __init__(self, parent, onoff, lw, callback=None, *args, **kwargs):
        self.lw = lw
        super().__init__(parent, onoff, callback, *args, **kwargs)
        self.lw.register_user(self)

    def draw_interior(self):
        self.create_rectangle((0, 0, ICON_SIZE, ICON_SIZE), fill='#FFFFFF', outline='#FFFFFF')
        self.create_line((0, ICON_SIZE // 2, ICON_SIZE, ICON_SIZE // 2), fill='black', width=self.lw.get())


class ImageButtonMixin(object):

    def __init__(self, image_map):
        self.images = {key: self.prepare_image(value) for key, value in image_map.items()}

    def prepare_image(self, image, background='#FFFFFF'):
        image_path = pkg_resources.resource_filename('ipysketch', os.path.join('assets', image))
        png = Image.open(image_path).convert('RGBA')
        background = Image.new('RGBA', png.size, background)
        alpha_composite = Image.alpha_composite(background, png)
        img = alpha_composite.resize((ICON_SIZE, ICON_SIZE), Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)


class ActionButton(SelectableButton, ImageButtonMixin):

    def __init__(self, parent, onoff, image, callback=None, *args, **kwargs):

        if image is None:
            raise Exception('No image given')

        ImageButtonMixin.__init__(self, {
            'normal': image
        })

        SelectableButton.__init__(self, parent, onoff, *args, callback=callback, **kwargs)
        self.draw()

    def draw_interior(self):
        self.create_image(1, 1, anchor=tk.NW, image=self.images['normal'])


class SimpleIconButton(ToolbarButton, ImageButtonMixin):

    def __init__(self, frame, image_map, statevar, callback):

        ImageButtonMixin.__init__(self, image_map)
        self.statevar = statevar

        ToolbarButton.__init__(self, frame, statevar, callback)

    def draw_interior(self):
        state = self.statevar.get()
        self.create_image(1, 1, anchor=tk.NW, image=self.images[state])


class SaveButton(SimpleIconButton):

    def __init__(self, frame, dirty, callback):
        self.dirty = dirty

        def wrapper(event):
            if self.dirty.get():
                callback(event)

        super().__init__(frame, {
            'normal': 'save-60.png',
            'disabled': 'save-disabled-60.png'
        }, dirty, wrapper)

    def draw_interior(self):
        if self.dirty.get():
            self.create_image(1, 1, anchor=tk.NW, image=self.images['normal'])
        else:
            self.create_image(1, 1, anchor=tk.NW, image=self.images['disabled'])


class LineWidthChooserDialog(tk.Toplevel):

    def __init__(self, parent, initial_lw=2, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        frame = ttk.Frame(self, border=0)
        frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.canvas = LineWidthChooser(frame, initial_lw)
        self.canvas.grid(row=0, column=0, columnspan=2, sticky=('WE'))

        ttk.Button(frame, text='OK', command=self.on_ok).grid(row=1, column=1, sticky='EW')
        ttk.Button(frame, text='Cancel', command=self.on_cancel).grid(row=1, column=0, sticky='WE')

        self._linewidth = initial_lw

        x, y = parent.winfo_x(), parent.winfo_y()
        self.geometry('+%d+%d' % (x + 200, y + 60))

    def get(self):
        if self._linewidth:
            return self.canvas.get()

    def on_cancel(self):
        self._linewidth = None
        self.destroy()

    def on_ok(self):
        self.destroy()


class LineWidthChooser(tk.Canvas):

    def __init__(self, parent, init_width, *args, **kwargs):
        self.width = 200
        self.height = 50
        super().__init__(parent, *args, width=self.width, height=self.height, border=0, **kwargs)
        self.line_width = init_width
        self.bind('<Button-1>', self.on_button_down)
        self.bind('<B1-Motion>', self.on_move)
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = self.width, self.height
        h -= 5
        self.create_polygon((5, (h+5)//2, w, 5, w, h), fill='black')
        x = self._calc_position()
        self.create_rectangle((x-3, 5, x+3, h), fill='grey', outline='red')

    def _calc_linewidth(self, x):
        return (x-5) / (self.width - 5) * 30

    def _calc_position(self):
        return self.line_width / 30 * (self.width-5) + 5

    def on_button_down(self, event):
        self.line_width = self._calc_linewidth(event.x)
        self.draw()

    def on_move(self, event):
        self.line_width = self._calc_linewidth(event.x)
        self.draw()

    def get(self):
        return self.line_width

    def set(self, value):
        self.line_width = value
        self.draw()
