import pkg_resources

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Ellipse, Rectangle
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.slider import Slider

from skimage.io import imread, imsave, imshow

from ipysketch.model import SketchModel, Path

MODE_WRITE = 1
MODE_ERASE = 2

COLOR_LIGHT_GRAY = Color(0.9, 0.9, 0.9)
COLOR_WHITE = Color(1, 1, 1)
COLOR_BLACK = Color(0, 0, 0)


class IconButton(Button):

    def __init__(self, file_name, **kwargs):
        super(IconButton, self).__init__(**kwargs)
        icon = pkg_resources.resource_filename('ipysketch', file_name)
        self.text = ''
        self.size = 60, 60
        self.size_hint = None, None
        self.background_normal = str(icon)


def pack_points(points):
    packed = []
    for i in range(0, len(points), 2):
        packed.append((points[i], points[i+1]))
    return packed


class CustomLine(Line):

    def __init__(self, *args, **kwargs):
        super(CustomLine, self).__init__(*args, **kwargs)

    def collides_with_circle(self, circle):
        points = pack_points(self.points)
        for p in points:
            if circle.is_inside(p):
                return True
        return False

class Circle(Ellipse):

    def __init__(self, center, radius, **kwargs):
        super(Circle, self).__init__(angle_start=0, angle_end=360, size=(radius, radius),
                                     pos=tuple(center), **kwargs)
        self.center = center
        self.radius = radius

    def is_inside(self, pt):
        if (self.center[0] - pt[0])**2 + (self.center[1] -pt[1])**2 < self.radius**2:
            return True
        return False


class ToolbarGrid(StackLayout):

    def __init__(self, **kwargs):
        super(ToolbarGrid, self).__init__(**kwargs)

        self.size_y = 60
        self.size_hint_y = None
        self.save_btn = IconButton('assets/save-60.png')
        self.add_widget(self.save_btn)

        self.pen_btn = IconButton('assets/pen-60.png')
        self.add_widget(self.pen_btn)

        self.eraser_btn = IconButton('assets/eraser-60.png')
        self.add_widget(self.eraser_btn)

        self.line_width_slider = Slider(min=1, max=10, value=3, size=(400, 60), size_hint=(None, None))
        self.add_widget(self.line_width_slider)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SketchPadWidget(BoxLayout):

    def __init__(self, file_name,  **kwargs):
        super(SketchPadWidget, self).__init__(**kwargs)


        self.orientation = 'vertical'
        self.mode = MODE_WRITE
        self.file_name = file_name

        self.toolbar = ToolbarGrid()
        self.toolbar.save_btn.bind(on_press=self.save)
        self.toolbar.pen_btn.bind(on_press=self.set_write_mode)
        self.toolbar.eraser_btn.bind(on_press=self.set_erase_mode)

        self.add_widget(self.toolbar)

        self.sketch_canvas = SketchCanvasWidget(file_name)
        self.add_widget(self.sketch_canvas)

        self.bind(
            size=self._update_rect,
            pos=self._update_rect
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def save(self, obj):
        if self.file_name.endswith('.isk'):
            basename = self.file_name[:-4]
        else:
            basename = self.file_name
        self.sketch_canvas.save(basename)
        self.export_to_png(basename + '.png')

        img = imread(basename + '.png')
        img = img[60:, :]
        imsave(basename + '.png', img)


    def clear(self, obj):
        self.sketch_canvas.clear()
        self.mode = MODE_WRITE

    def set_erase_mode(self, obj):
        self.mode = MODE_ERASE

    def set_write_mode(self, obj):
        self.mode = MODE_WRITE


class SketchCanvasWidget(BoxLayout):

    def __init__(self, file_name, **kwargs):
        super(SketchCanvasWidget, self).__init__(**kwargs)
        Window.set_system_cursor('crosshair')
        self.sketch = SketchModel()
        self.line_path_map = {}
        self.load(file_name)
        self.bind(
            size=self._update_rect,
            pos=self._update_rect
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_touch_down(self, touch):

        if not self.collide_point(touch.x, touch.y):
            with self.canvas:
                pass # workaround to allow drawing after clearing image
                     # otherwise only the canvas.before stuff is carried out, setting only the white background
            return

        if self.parent.mode == MODE_WRITE:

            line_width = self.parent.toolbar.line_width_slider.value

            touch.ud['path'] = path = Path(line_width)
            path.add_point(touch.x, touch.y)

            with self.canvas:
                self.canvas.add(Color(0, 0, 0))
                line = CustomLine(points=(touch.x, touch.y), width=line_width)
                self.line_path_map[line] = path
                line
                touch.ud['line'] = line

        else:
            eraser_radius = 10
            circle = Circle((touch.x-eraser_radius/2, touch.y-eraser_radius/2), eraser_radius)
            touch.ud['line'] = circle
            #self.canvas.add(COLOR_LIGHT_GRAY)
            #self.canvas.add(circle)
            self.remove_paths_at(circle)

    def on_touch_move(self, touch):
        if self.parent.mode == MODE_WRITE:
            if self.collide_point(touch.x, touch.y) and 'line' in touch.ud:
                touch.ud['path'].add_point(touch.x, touch.y)
                touch.ud['line'].points += [touch.x, touch.y]
        else:
            if 'line' not in touch.ud:
                return
            circle = touch.ud['line']
            center = touch.x-circle.radius / 2, touch.y - circle.radius/2
            circle.pos = center
            circle.center = center
            self.remove_paths_at(circle)

    def on_touch_up(self, touch):
        if self.parent.mode == MODE_WRITE:
            if 'path' in touch.ud:
                self.sketch.add_path(touch.ud['path'])

    def remove_paths_at(self, circle):
        lines_to_remove = []
        for line in self.canvas.children:
            if isinstance(line, CustomLine):
                if line.collides_with_circle(circle):
                    lines_to_remove.append(line)

        for line in lines_to_remove:
            self.canvas.remove(line)
            self.sketch.paths.remove(self.line_path_map[line])

    def save(self, basename):
        self.sketch.save(basename)

    def load(self, file_name):
        self.sketch.load(file_name)
        color = (0, 0, 0)

        with self.canvas:
            Color(*color)
            for path in self.sketch.paths:
                line = CustomLine(points=path.points_flattened(), width=path.line_width)
                line
                self.line_path_map[line] = path

    def clear(self):
        self.sketch.clear()
        self.canvas.clear()

        self.bind(
            size=self._update_rect,
            pos=self._update_rect
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)


class SketchApp(App):

    def __init__(self, file_name, **kwargs):
        super(SketchApp, self).__init__(**kwargs)
        self.file_name = file_name

    def build(self):
        return SketchPadWidget(self.file_name)



def start_app(name):
    SketchApp(name).run()
