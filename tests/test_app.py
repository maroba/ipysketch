import unittest

from ipysketch.app import Application, main


class TestApplication(unittest.TestCase):

    def setUp(self) -> None:
        self.app = None

    def tearDown(self) -> None:
        self.app.update()
        self.app.destroy()

    def test_app_starts_in_drawing_mode(self):

        self.app = Application('abc')
        app = self.app

        app.update()


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

        self.app = Application('abc')
        app = self.app

        app.update()

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
        self.app = Application('abc')
        app = self.app

        app.update()

        canvas = app.canvas_controller.canvas

        mouse_action(canvas, (
            100, 100,
            110, 120,
            120, 140,
            200, 200
        ))

        app.action_controller.buttons[1].event_generate('<Button-1>')

        mouse_action(canvas, (105, 125, 105, 126, 105, 125))

        app.undo(None)

        app.update()

        self.assertEqual(1, len(app.model.paths))

        app.redo(None)

        app.update()

        self.assertEqual(0, len(app.model.paths))



def mouse_action(canvas, points_flat):
    canvas.event_generate('<Button-1>', x=points_flat[0], y=points_flat[1])
    for i in range(2, len(points_flat)-2, 2):
        canvas.event_generate('<B1-Motion>', x=points_flat[i], y=points_flat[i+1])
    canvas.event_generate('<ButtonRelease-1>', x=points_flat[-2], y=points_flat[-1])


if __name__ == '__main__':
    unittest.main()
