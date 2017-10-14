'''Tests'''

import unittest
import difflib
import json
from addon import Addon
from addon import Frontend
from deezerbackend import DeezerBackend

class MockFrontend(Frontend):
    '''mock frontend class'''

    def __init__(self):
        Frontend.__init__(self)
        self._items = []
        self._settings = {'stream_url': 'http://stream/{track_id}'}
        self._keyboard_input = 'test input'

    def get_setting(self, key):
        return self._settings.get(key, None)

    def get_keyboard_input(self, message):
        return self._keyboard_input

    def render(self, items):
        if not items:
            raise Exception('no None type expected')
        self._items = items

class TestAddon(unittest.TestCase):

    def setUp(self):
        self._frontend = MockFrontend()
        backend = DeezerBackend(self._frontend, self)
        self._addon = Addon(backend, self._frontend, debug=True)
        self._url_2_json = {'stream_url':''}

    def load_json(self, url):
        return self._url_2_json.pop(url)

    def assertResult(self, aaa):
        #bbb = []
        #bbb.extend(self._frontend._items)
        bbb = self._frontend._items
        try:
            self.assertSequenceEqual(aaa, bbb)
        except Exception:
            diff = difflib.unified_diff(
                json.dumps(bbb, sort_keys=True, indent=4).splitlines(1),
                json.dumps(aaa, sort_keys=True, indent=4).splitlines(1)
            )
            raise Exception(''.join(diff))

    def test_root(self):
        self._addon.render('')
        self.assertResult([
            {'label': 'Search', 'target': {'mode': 'search'}},
            {'label': 'Albums', 'target': {'mode': 'albums'}}
        ])

    def test_top_albums(self):
        self._url_2_json['http://api.deezer.com/chart/0?limit=20&index=20'] = {
                "albums":
                {
                    "data":
                    [
                        {
                            "id":"album-id", 
                            "cover_big": "album-cover",
                            "title": "album-title",
                            "type": "album",
                            "artist": {
                                "id":"artist-id",
                                "name":"artist-name",
                                "picture_big": "artist-pic",
                                "type": "artist"
                            }
                        }
                    ]
                },
                "total": "41"
            }
        self._addon.render('?mode=albums&page=1')
        self.assertResult(
            [{'target': {'mode': 'album', 'album_id': 'album-id'}, 'thumb': 'album-cover', 'label': 'album-title - artist-name'},
             {'target': {'mode': 'albums', 'page': 2}, 'label': 'page 3'}])

    def test_album(self):
        self._url_2_json['http://api.deezer.com/album/302127'] = {
                "id": "302127",
                "title": "album_title",
                "nb_tracks": "14",
                "release_date": "2001-02-03",
                "cover_big": "album-cover",
                "type": "album",
                "artist": {
                    "id": "artist-id",
                    "name": "artist-name"
                },
                "tracks": {
                    "data": [
                        {
                            "id": "track-id",
                            "title": "track-title",
                            "duration": "320"
                        },
                        {
                            "id": "track-id2",
                            "title": "track-title2",
                            "duration": "321"
                        }
                    ]
                }
            }
        self._addon.render('?mode=album&album_id=302127')
        self.assertResult([
            # {'target': {'mode': 'like_album', 'album_id': '302127'}, 'label': u'\u2764 Like album'},
            {
                'label': '1. track-title',
                'thumb': 'album-cover', 
                'track_count': '14', 
                'title': 'track-title', 
                'url': 'http://stream/track-id',
                'artist': 'artist-name', 
                'year': '2001', 
                'duration': 320, 
                'tracknumber': 1, 
                'album': 'album_title'
            },{
                'label': '2. track-title2',
                'thumb': 'album-cover', 
                'track_count': '14', 
                'title': 'track-title2', 
                'url': 'http://stream/track-id2',
                'artist': 'artist-name', 
                'year': '2001', 
                'duration': 321, 
                'tracknumber': 2, 
                'album': 'album_title'
            }])

    def test_initial_search(self):
        self._url_2_json['http://api.deezer.com/search/artist?q=test%20input&limit=20&index=0'] = {
            "data": [{
                "id": "artist-id",
                "name": "artist-name",
                "picture_big": "artist-picture",
                "type": "artist"
            }],
            "total": "21"
        }
        self._addon.render('?mode=search')
        self.assertResult(
            [
                {'target': {'mode': 'artist', 'artist_id': 'artist-id'}, 'thumb': 'artist-picture', 'label': 'artist-name'},
                {'target': {'query': 'test input', 'mode': 'search', 'page': 1}, 'label': 'page 2'}
            ])

    def test_continued_search(self):
        self._url_2_json['http://api.deezer.com/search/artist?q=xxx&limit=20&index=20'] = {
            "data": [{
                "id": "artist-id",
                "name": "artist-name",
                "picture_big": "artist-picture",
                "type": "artist"
            }],
            'total': '21'
        }
        self._addon.render('?mode=search&query=xxx&page=1')
        self.assertResult([
            {'target': {'mode': 'artist', 'artist_id': 'artist-id'}, 'thumb': 'artist-picture', 'label': 'artist-name'}
        ])

    def test_track(self):
        self._url_2_json['http://api.deezer.com/track/track-id'] = {
            'id': 'track-id',
            'title': 'track-title',
            'track_position': 5,
            'duration': 42,
            'release_date': '2001-02-03',
            'album': {
                'id': 'album_id',
                'title': 'album-title',
                'cover_big': 'album-cover'
            },
            'artist': {
                'name': 'artist-name'
            }
        }
        self._addon.render('?mode=track&track_id=track-id')
        self.assertResult([{
            'label': '5. track-title',
            'artist': 'artist-name',
            'thumb': 'album-cover',
            'title': 'track-title',
            'url': 'http://stream/track-id',
            'year': '2001',
            'duration': 42,
            'tracknumber': 5,
            'album': 'album-title'
        }])

if __name__ == '__main__':
    unittest.main()
