import sys
from ipysketch.kivyapp import SketchApp

if __name__ == '__main__':
    try:
        sketch_name = sys.argv[1]
    except:
        print('Invalid or missing sketch name.')
        sys.exit(1)

    SketchApp(sketch_name).run()

