import tkinter as tk
import pkg_resources

import pickle
import os
import sys
import io
from PIL import Image, ImageTk

from ipysketch.controller import ColorButtonGroupController, ActionButtonGroupController, \
    CanvasController, LineWidthButtonGroupController
from ipysketch.canvas import ObjectVar
from ipysketch.buttons import SimpleIconButton, SaveButton
from ipysketch.constants import *
from ipysketch.model import Pen, SketchModel, History


class Application(tk.Tk):
    """ The Sketch Pad App """

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The name of the sketch. Used as basename for the image files.
        if not name:
            raise Exception('No sketch name given.')
        self.name = name

        self.history = self._create_model_history()

        self._create_toolbar()
        self._create_canvas()
        self._configure_window()

        self.wait_visibility()
        self.attributes('-topmost', False)
        icon = pkg_resources.resource_filename('ipysketch', os.path.join('assets', 'logo.ico'))
        if sys.platform.startswith('win'):
            self.iconbitmap(icon)
        png = pkg_resources.resource_filename('ipysketch', os.path.join('assets', 'logo.png'))
        png = Image.open(png)
        self.iconphoto(True, ImageTk.PhotoImage(png))
        self.title('ipysketch ' + name)

    def _configure_window(self):
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.geometry('800x600+100+100')
        self.lift()
        self.attributes('-topmost', True)

    def _create_canvas(self):
        frame = tk.Frame(self, border=4)
        frame.grid(row=1, column=0, sticky='NWSE')
        self.canvas_controller = CanvasController(self, frame)

    def _create_toolbar(self):
        """Sets up the toolbar and its controllers."""

        # Put everything in a content frame
        frame = tk.Frame(self, border=3)
        frame.grid(row=0, column=0, sticky='WE')

        # Set up the save button
        self.dirty = ObjectVar()
        self.dirty.set(False)
        SaveButton(frame, self.dirty, self.save).pack(side=tk.LEFT)

        # Set up the button group for drawing, erasing, lasso selection and
        # shifting the canvas
        self.action_controller = ActionButtonGroupController(frame)
        self.action_controller.onoffvars[0].set(True)

        # Set up undo and redo buttons
        self.undo_var = ObjectVar()
        self.undo_var.set('normal')
        self.redo_var = ObjectVar()
        self.redo_var.set('normal')
        SimpleIconButton(frame, {'normal': 'undo-50.png'}, self.undo_var, self.undo).pack(side=tk.LEFT)
        SimpleIconButton(frame, {'normal': 'redo-50.png'}, self.redo_var, self.redo).pack(side=tk.LEFT)

        # Set up the color selection buttons
        self.colors_controller = ColorButtonGroupController(frame)
        self.colors_controller.onoffvars[0].set(True)

        # Set up the line selection buttons
        self.linewidth_controller = LineWidthButtonGroupController(frame, self)
        self.linewidth_controller.onoffvars[0].set(True)

    def _create_model_history(self):
        """ Start a history of sketch models and optionally initialize it with a given sketch.

        :return: History object of models
        """
        file_name = self.name + '.isk'
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                model = pickle.load(f)
        else:
            model = SketchModel()

        return History(model)

    @property
    def model(self):
        """ Property for returning the current model in the model history. """
        return self.history.current()

    @property
    def action(self):
        """ Return a constant indicating which mode is currently active. """
        selected = self.action_controller.get_selected()[0]
        if selected == 0:
            return ACTION_DRAW
        elif selected == 1:
            return ACTION_ERASE
        elif selected == 2:
            return ACTION_LASSO
        elif selected == 3:
            return ACTION_MOVE
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
        elif value == ACTION_MOVE:
            self.action_controller.set(3)

    @property
    def pen(self):
        """ Return a Pen object with the currently selected color and line width. """
        color = self.colors_controller.get()
        width = self.linewidth_controller.get()
        return Pen(color=color, width=width)

    def save(self, event):
        """ Save the current model to files."""

        with open(os.path.join(os.curdir, self.name + '.isk'), 'wb') as f:
            pickle.dump(self.canvas_controller.model, f)

        png_name = os.path.join(os.curdir, self.name + '.png')
        # If an empty model shall be saved, we should delete the PNG
        # so that the Jupyter cell does not display an obsolete version:
        if len(self.model.paths) == 0:
            if os.path.exists(png_name):
                os.remove(png_name)
            self.dirty.set(False)
            return

        ps = self._canvas_to_postscript_cropped()
        img = Image.open(io.BytesIO(ps.encode('utf-8')))

        img.resize(img.size, resample=3)
        img.save(png_name)

        self.dirty.set(False)


    def _canvas_to_postscript_cropped(self):
        bbox = self.model.bbox()
        w = bbox.lr.x - bbox.ul.x
        h = bbox.lr.y - bbox.ul.y
        ps = self.canvas_controller.canvas.postscript(colormode='color',
                                                      x=bbox.ul.x - 20, y=bbox.ul.y - 20,
                                                      width=w + 40, height=h + 40)
        return ps

    def undo(self, event):
        """Callback for the undo button."""
        self.history.back()
        self.canvas_controller.update_canvas()

    def redo(self, event):
        """Callback for the redo button."""
        self.history.forward()
        self.canvas_controller.update_canvas()

    def trigger_dirty(self):
        """Callback for when a changing action has started."""
        self.history.new()
        self.dirty.set(True)


def main(name):
    """ The main function to start the app. """
    app = Application(name)
    app.mainloop()

