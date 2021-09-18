import sys
from ipysketch.app import main

if __name__ == '__main__':
    try:
        name = sys.argv[1]
        if not name:
            raise Exception
    except:
        print('Invalid or missing sketch name')
        sys.exit(1)
    main(name)

