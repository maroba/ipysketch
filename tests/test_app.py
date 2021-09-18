import unittest
import os

from ipysketch.app import Application, main


class TestApplication(unittest.TestCase):

    def setUp(self) -> None:
        self.app = Application('abc')
        self.app.update()

    def tearDown(self) -> None:
        self.app.update()
        self.app.destroy()

    def test_app_starts_in_drawing_mode(self):

        app = self.app

        canvas = app.canvas_controller.canvas

        mouse_action(canvas, (
            100, 100,
            110, 120,
            120, 140,
            200, 200
        ))

        app.update()

        self.assertEqual(1, len(app.model.paths))

    def test_erase_path(self):

        app = self.app

        canvas = app.canvas_controller.canvas

        mouse_action(canvas, (
            100, 100,
            110, 120,
            120, 140,
            200, 200
        ))

        app.action_controller.buttons[1].event_generate('<Button-1>')

        mouse_action(canvas, (105, 125, 105, 126, 105, 125))

        app.update()

        self.assertEqual(0, len(app.model.paths))

    def test_undo_redo(self):
        app = self.app

        canvas = app.canvas_controller.canvas

        mouse_action(canvas, (
            100, 100,
            110, 120,
            120, 140,
            200, 200
        ))

        self.change_to_mode('erase')

        mouse_action(canvas, (105, 125, 105, 126, 105, 125))

        app.undo(None)

        app.update()

        self.assertEqual(1, len(app.model.paths))

        app.redo(None)

        app.update()

        self.assertEqual(0, len(app.model.paths))

    def test_select_path(self):
        app = self.app
        canvas = app.canvas_controller.canvas

        self.draw_round_triangle(canvas)

        self.change_to_mode('lasso')

        self.select_round_triangle(canvas)

        app.update()

        self.assertEqual(1, len(app.canvas_controller.selection))

    def test_move_object(self):

        app = self.app
        canvas = app.canvas_controller.canvas

        self.draw_round_triangle(canvas)

        self.change_to_mode('lasso')

        self.select_round_triangle(canvas)

        mouse_action(canvas, (
            100, 100,
            200, 200,
            200, 200
        ))

        app.update()

        self.assertEqual(app.model.paths[0].points[0].x, 200)
        self.assertEqual(app.model.paths[0].points[0].y, 200)

    def test_save_drawing(self):

        self.draw_round_triangle(self.app.canvas_controller.canvas)
        self.app.save(None)

        self.app.update()

        self.assertTrue(os.path.exists('abc.png'))
        self.assertTrue(os.path.exists('abc.isk'))

        os.remove('abc.png')
        os.remove('abc.isk')

    def select_round_triangle(self, canvas):
        mouse_action(canvas, (
            100, 90,
            40, 160,
            160, 160,
            100, 90
        ))

    def draw_round_triangle(self, canvas):
        mouse_action(canvas, (
            100, 100,
            50, 150,
            150, 150,
            100, 100
        ))

    def change_to_mode(self, mode):

        if mode == 'draw':
            self.app.action_controller.buttons[0].event_generate('<Button-1>')
        elif mode == 'erase':
            self.app.action_controller.buttons[1].event_generate('<Button-1>')
        elif mode == 'lasso':
            self.app.action_controller.buttons[2].event_generate('<Button-1>')



def mouse_action(canvas, points_flat):
    canvas.event_generate('<Button-1>', x=points_flat[0], y=points_flat[1])
    for i in range(2, len(points_flat)-2, 2):
        canvas.event_generate('<B1-Motion>', x=points_flat[i], y=points_flat[i+1])
    canvas.event_generate('<ButtonRelease-1>', x=points_flat[-2], y=points_flat[-1])


if __name__ == '__main__':
    unittest.main()
