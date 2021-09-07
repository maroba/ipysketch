import os
import subprocess
import sys

from ipywidgets import Button, Image, Output, DOMWidget
from IPython.display import display

# IMPORTANT:
#
#    jupyter nbextension install --user --py widgetsnbextension
#    jupyter nbextension enable --py widgetsnbextension
#

class Sketch(DOMWidget):

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.edit_button = Button(description='Edit')
        self.edit_button.on_click(self.handle_edit)
        self.output = Output()
        if os.path.exists(name + '.png'):
            self.img = Image.from_file(name + '.png')
        else:
            self.img = None

    def handle_edit(self, e):
        with self.output:
            print('Starting sketch pad...')
        python = sys.executable
        proc = subprocess.Popen((python + ' -m ipysketch ' + self.name).split(), shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
        proc.wait()
        self.output.clear_output()
        self.close()

        self.edit_button = Button(description='Edit')
        self.edit_button.on_click(self.handle_edit)
        self.output = Output()
        if os.path.exists(self.name + '.png'):
            self.img = Image.from_file(self.name + '.png')
        else:
            self.img = None
        self.open()

        self.show()

    def open(self, **kwargs):
        self.edit_button.open()
        self.output.open()
        if self.img:
            self.img.open()

    def close(self, **kwargs):
        self.edit_button.close()
        self.output.close()
        if self.img:
            self.img.close()

    def show(self, **kwargs):
        display(self.edit_button, self.output)
        if self.img:
            display(self.img)

    def _ipython_display_(self, **kwargs):
        self.show(**kwargs)
