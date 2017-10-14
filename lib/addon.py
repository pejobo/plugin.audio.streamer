# https://docs.python.org/2.7/
import sys
import urlparse

class Addon:

    def __init__(self, backend, frontend, debug=False):
        self._backend = backend
        self._frontend = frontend
        self._frontend.debug(debug)

    def log(self, message):
        self._frontend.log(message)

    def render(self, url):
        mode = None
        try:
            args =  urlparse.parse_qs(url[1:])
            for key in args:
                args[key] = args[key][0]

            mode = args.get(Backend.MODE, None)
            if mode is None:
                self.log('no arguments -> render root dir')
                items = self._backend.root()
            else:
                self.log('arguments: ' + str(args))
                args.pop(Backend.MODE)
                items = getattr(self._backend, mode)(**args)
            if items:
                self._frontend.render(list(items))
        finally:
            pass

    def main(self):
        self.log(sys.argv)
        self.render(sys.argv[2])

        
class Backend:
    """Empty audio backend"""

    LABEL = 'label'
    MODE = 'mode'
    THUMB = 'thumb'
    URL = 'url'
    TARGET = 'target'
    TRACK_TITLE = 'title'
    TRACK_NUM = 'tracknumber'
    DURATION = 'duration'
    ALBUM_NAME = 'album'
    YEAR = 'year'
    ARTIST = 'artist'

    def __init__(self, frontend):
        self._frontend = frontend

    def log(self, message):
        self._frontend.log(message)

    def root(self):
        """list of root menu entries"""
        return []

class Frontend:
    """Frontend functions"""

    def __init__(self, debug=False):
        self._debug = debug

    def get_setting(self, name):
        """request setting value"""
        raise NotImplementedError

    def set_setting(self, name, value):
        """set setting value"""
        raise NotImplementedError

    def debug(self, value):
        self._debug = value

    def log(self, message):
        """log the provided message if debugging is switched on"""
        if self._debug:
            print(str(message))

    def get_keyboard_input(self, message):
        """request user input"""
        raise NotImplementedError

    def render(self, items):
        """render a list of items"""
        raise NotImplementedError

    def build_url(self, params):
        """"build a callback url for the provided params"""
