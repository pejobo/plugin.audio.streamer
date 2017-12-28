# coding=UTF-8
""""Deezer Backend"""

import inspect
import json
from random import shuffle
import requests
from lib.addon import Backend

class DeezerBackend(Backend):
    """Deezer backend"""

    ALBUM_TRACK_COUNT = 'track_count'
    API_STREAMING_URL = 'http://tv.deezer.com/smarttv/streaming.php'

    def __init__(self, frontend, requester=None):
        Backend.__init__(self, frontend)
        self._access_token = frontend.get_setting('access_token')
        # http://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html
        self._user_id = frontend.get_setting('user_id')
        if self._user_id == '' and self._access_token != '':
            self._user_id = self._load_json('http://api.deezer.com/user/me', {'access_token': self._access_token})['id']
            # todo: safe user id in settings
        if hasattr(self, '_user_id'):
            self.log('user id is %s' % self._user_id)
        self._stream_url = frontend.get_setting('stream_url')
        self._requester = requester if requester else self

    def load_json(self, url, params={}):
        self._frontend.log('loading json ' + url)
        content = requests.get(url, params=params).text
        self.log('loaded: ' + content[:40] + '...')
        return json.loads(content)

    def _to_boolean(self, x):
        if x == 'True' or x is True:
            return True
        if x == None:
            return None
        return False

    def _ternary(self, bool_or_none, true_val, false_val, none_val):
        b = self._to_boolean(bool_or_none)
        if b is True:
            return true_val
        if b is False:
            return false_val
        return none_val

    def _like(self, bool, text):
        return self._ternary(
            bool,
            u'❤ Like: ' + text,
            u'💔 Unlike: ' + text,
            text
        )

    def _load_json(self, url, params={}):
        """Loads the content from the provided url and parse it as json"""
        return self._requester.load_json(url)

    def load(self, url, params={}):
        self._frontend.log('loading ' + url)
        content = requests.get(url, params=params).text
        self.log('loaded: ' + content[:40] + '...')
        return content

    def _extract_artist(self, artist, like=None):
        target = {
            self.MODE: self._ternary(like, self.like_artist.__name__, self.unlike_artist.__name__, self.artist.__name__),
            'artist_id': artist['id']
        }
        if  like != None:
            target['like'] = like
        return {
            self.LABEL: self._like(like, artist['name']),
            self.THUMB: artist['picture_big'],
            self.TARGET: target
        }

    def _extract_album_data(self, album_data, artist_data):
        data = {
            self.ALBUM_NAME: album_data['title'],
            self.ARTIST: artist_data['name'],
            self.THUMB: None,
            self.YEAR: None,
            self.ALBUM_TRACK_COUNT: None
        }
        if 'cover_big' in album_data:
        	data[self.THUMB] = album_data['cover_big']
        if 'nb_tracks' in album_data:
            data[self.ALBUM_TRACK_COUNT] = album_data['nb_tracks']
        if 'release_date' in album_data:
            data[self.YEAR] = album_data.get('release_date', '')[:4]
        return data

    def _extract_album(self, album, artist={}, like=None):
        label = self._like(like, album['title'])
        if 'name' in artist:
            label += ' - %s' % artist['name']
        elif 'artist' in album:
            label += ' - %s' % album['artist']['name']
        if 'release_date' in album:
            label += ' (%s)' % (album['release_date'][:4])
        function = self._ternary(like, self.like_album, self.unlike_album, self.album)
        return {
            self.LABEL: label,
            self.THUMB: album['cover_big'],
            self.TARGET: {
                self.MODE: function.__name__,
                'album_id': album['id']
            }
        }

    def _extract_playlist(self, playlist, like=None):
        label = self._like(like, playlist['title'])
        function = self._ternary(like, self.like_playlist, self.unlike_playlist, self.playlist)
        return {
            self.LABEL: label,
            self.THUMB: playlist['picture_big'],
            self.TARGET: {
                self.MODE: function.__name__,
                'playlist_id': playlist['id']
            }
        }

    def _next_page(self, page, total, items_per_page, additional_target_params={}):
        page = int(page)
        next_page = page + 1
        if int(total) > (next_page * int(items_per_page)):
            target = inspect.currentframe().f_back.f_code.co_name
            target_data = {self.MODE: target, 'page': next_page}
            target_data.update(additional_target_params)
            yield {self.LABEL: 'page ' + str(next_page + 1), self.TARGET: target_data}

    def check_stream_url(self):
        if self._stream_url:
            try:
                self._requester.load_json(self._stream_url.format(track_id=0))
            except ValueError:
                pass

    def root(self):
        """root menu"""
        yield {self.LABEL: 'Search', self.TARGET: {self.MODE: self.search.__name__}}
        yield {self.LABEL: 'Albums', self.TARGET: {self.MODE: self.albums.__name__}}
        if self._user_id:
            yield {self.LABEL: 'My artists', self.TARGET: {self.MODE: self.my_artists.__name__}}
            yield {self.LABEL: 'My albums', self.TARGET: {self.MODE: self.my_albums.__name__}}
            yield {self.LABEL: 'My playlists', self.TARGET: {self.MODE: self.my_playlists.__name__}}
            yield {self.LABEL: u'💔 Remove likes', self.TARGET: {self.MODE: self.remove_likes.__name__}}

    def remove_likes(self):
        """Remove likes for artists, albums, playlists"""
        yield {self.LABEL: u'💔 Remove artist likes', self.TARGET: {self.MODE: self.my_artists.__name__, 'like': False}}
        yield {self.LABEL: u'💔 Remove album likes', self.TARGET: {self.MODE: self.my_albums.__name__, 'like': False}}
        yield {self.LABEL: u'💔 Remove playlists likes', self.TARGET: {self.MODE: self.my_playlists.__name__, 'like': False}}

    def unlike_artists(self, page=0):
        """Menu to remove artists from likes"""
        url = 'https://api.deezer.com/user/me/artists?&limit=20&index=%i'
        data = self._load_json(url % int(page)* 20, {'access_token': self._access_token})
        for artist in data['data']:
            yield self._extract_artist(artist, like=False)
        for next_page in self._next_page(int(page), int(data['total']), 20):
            yield next_page

    def _get_me_url(self):
        return 'https://api.deezer.com/user/' + self._user_id

    def my_artists(self, page=0, like=None):
        """Favorite artists"""
        url = self._get_me_url() + '/artists?&limit=20&index=%i'
        data = self._load_json(url % int(page) * 20, {'access_token': self._access_token})
        if 'data' in data:
            for artist in data['data']:
                yield self._extract_artist(artist, like=like)
            for next_page in self._next_page(int(page), int(data['total']), 20):
                yield next_page

    def my_albums(self, page=0, like=None):
        """Favorite albums"""
        url = self._get_me_url() + '/albums?&limit=20&index=%i'
        data = self._load_json(url % int(page) * 20, {'access_token': self._access_token})
        if 'data' in data:
            for album in data['data']:
                yield self._extract_album(album, like=like)
            for next_page in self._next_page(int(page), int(data['total']), 20):
                yield next_page

    def my_playlists(self, page=0, like=None):
        """Favorite playlists"""
        url = self._get_me_url() + '/playlists?&limit=20&index=%i'
        data = self._load_json(url % int(page) * 20, {'access_token': self._access_token})
        if 'data' in data:
            for playlist in data['data']:
                yield self._extract_playlist(playlist, like=like)
            for next_page in self._next_page(int(page), int(data['total']), 20):
                yield next_page

    def search(self, query=None, page=0):
        """Request user input and search for it"""
        if query is None:
            query = self._frontend.get_keyboard_input('Search')
            if not query:
                return
        url = 'http://api.deezer.com/search/artist?q=%s&limit=20&index=%i'
        data = self._load_json(url % (query.replace(' ', '%20'), int(page) * 20))
        if 'data' in data:
            for artist in data['data']:
                yield self._extract_artist(artist)
            for next_page in self._next_page(page, data['total'], 20, {'query': query}):
                yield next_page

    def albums(self, page=0):
        """List top albums"""
        data = self._load_json('http://api.deezer.com/chart/0?limit=20&index=%i' % (int(page) * 20))
        for album in data['albums']['data']:
            yield self._extract_album(album)
        for next_page in self._next_page(page, 2000, 20):
            yield next_page

    def playlist(self, playlist_id):
        """Display playlist content"""
        tracks = self._load_json('http://api.deezer.com/playlist/' + playlist_id)['tracks']['data']
        shuffle(tracks)
        for track in tracks:
            album_data = self._extract_album_data(track['album'], track['artist'])
            yield self._extract_track(track, -1, album_data, track['artist'])

    def album(self, album_id):
        """Load album data"""
        album = self._load_json('http://api.deezer.com/album/' + album_id)
        album_data = self._extract_album_data(album, album['artist'])
        index = 1
        for track in album['tracks']['data']:
            yield self._extract_track(track, index, album_data, album['artist'])
            index = index + 1

    def artist(self, artist_id, like=True):
        """Show menu: like artist, artist albumes, artist playlists"""
        if self._to_boolean(like):
            yield {
                self.LABEL: u'❤ Like',
                self.TARGET: {self.MODE: self.like_artist.__name__, 'artist_id': artist_id}
            }
        else:
            yield {
                self.LABEL: u'💔 Remove like',
                self.TARGET: {self.MODE: self.unlike_artist.__name__, 'artist_id': artist_id}
            }
        yield {
            self.LABEL: 'Albums',
            self.TARGET: {self.MODE: self.artist_albums.__name__, 'artist_id': artist_id}
        }
        yield {
            self.LABEL: 'Playlists',
            self.TARGET: {self.MODE: self.artist_playlists.__name__, 'artist_id': artist_id}
        }
        yield {
            self.LABEL: u'❤ Add album to favorits',
            self.TARGET: {self.MODE: self.artist_albums.__name__, 'artist_id': artist_id, 'like': True}
        }
        yield {
            self.LABEL: u'❤ Add playlist to favorits',
            self.TARGET: {self.MODE: self.artist_playlists.__name__, 'artist_id': artist_id, 'like': True}
        }

    def artist_albums(self, artist_id, page=0, like=None):
        url = 'http://api.deezer.com/artist/%s/albums?limit=20&index=%i'
        data = self.load_json(url % (artist_id, int(page) * 20))
        artist_data = self._load_json("http://api.deezer.com/artist/" + artist_id)
        for album in data['data']:
            yield self._extract_album(album, artist_data, like)
        for next_page in self._next_page(page, data['total'], 20, {'like': like}):
            yield next_page

    def artist_playlists(self, artist_id, page=0, like=None):
        url = 'http://api.deezer.com/artist/%s/playlists?limit=20&index=%i'
        data = self.load_json(url % (artist_id, int(page) * 20))
        if 'data' in data:
            for playlist in data['data']:
                yield self._extract_playlist(playlist, like)
            for next_page in self._next_page(page, data['total'], 20, {'like': like}):
                yield next_page

    def track(self, track_id):
        """"Load track data"""
        track = self._load_json('http://api.deezer.com/track/' + str(track_id))
        album = track['album']
        album['release_date'] = track['release_date']
        album = self._extract_album_data(album, track['artist'])
        yield self._extract_track(track, track['track_position'], album, track['artist'])

    def get_stream_url(self, track_id):
        if self._stream_url:
            return self._stream_url.format(track_id=track_id)
        return self.load(self.API_STREAMING_URL, {
            'access_token': self._access_token,
            'track_id': track_id,
            'device': 'panasonic'
        })

    def _extract_track(self, track_data, index, album, artist):
        result = {
            self.TRACK_TITLE: track_data['title'],
            self.ARTIST: artist['name'],
            self.DURATION: int(track_data['duration']),
            self.URL: self.get_stream_url(track_data['id'])
        }
        result.update(album)
        if index != -1:
            result[self.LABEL] = '%i. %s' % (index, track_data['title'])
            result[self.TRACK_NUM] = index
        else:
            result[self.LABEL] = '%s (%s)' % (track_data['title'], artist['name'])
        return result

    def like_artist(self, artist_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/artists&request_method=POST' % self._user_id,
            {'artist_id': artist_id, 'access_token': self._access_token}
        )
        self.log('liked artist %s: %i - %s' % (artist_id, response.status_code, response.content[:40]))

    def like_album(self, album_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/albums&request_method=POST' % self._user_id,
            {'album_id': album_id, 'access_token': self._access_token}
        )
        self.log('liked album %s: %i - %s' % (album_id, response.status_code, response.content[:40]))

    def like_playlist(self, playlist_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/playlists&request_method=POST' % self._user_id,
            {'playlist_id': playlist_id, 'access_token': self._access_token}
        )
        self.log('liked playlist %s: %i - %s' % (playlist_id, response.status_code, response.content[:40]))

    def unlike_artist(self, artist_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/artists&request_method=DELETE' % self._user_id,
            {'artist_id': artist_id, 'access_token': self._access_token}
        )
        self.log('unliked artist %s: %i - %s' % (artist_id, response.status_code, response.content[:40]))

    def unlike_album(self, album_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/albums&request_method=DELETE' % self._user_id,
            {'album_id': album_id, 'access_token': self._access_token}
        )
        self.log('unliked album %s: %i - %s' % (album_id, response.status_code, response.content[:40]))

    def unlike_playlist(self, playlist_id):
        response = requests.get(
            'https://api.deezer.com/user/%s/playlists&request_method=PODELETE' % self._user_id,
            {'playlist_id': playlist_id, 'access_token': self._access_token}
        )
        self.log('unliked playlist %s: %i - %s' % (playlist_id, response.status_code, response.content[:40]))
