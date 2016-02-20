import sys
import io
import spotipy
import spotipy.oauth2 as oauth2
import threading
import subprocess
import numpy
import urllib.request as urllib
from PIL import Image

from webserver import Web_Server

class Spotify_Model(object):
    
    def __init__(self, auth, scope='user-read-private'):
        self.spotify = spotipy.Spotify()
        self.username = auth['username']
        self.client_id = auth['client_id']
        self.client_secret = auth['client_secret']
        self.redirect_uri = auth['redirect_uri']
        self.scope = scope
        self.sp_oauth = None
        self.url = None
        self.authorize()

    def set_sp_oauth(self):
        self.sp_oauth = oauth2.SpotifyOAuth(self.client_id, self.client_secret, self.redirect_uri, scope=self.scope, cache_path=".cache-"+self.username)

    def authorize(self):
        access_token = self.get_access_token()

    def get_access_token(self):
        if not self.sp_oauth:
            self.set_sp_oauth()
        token_info = self.sp_oauth.get_cached_token()
        if not token_info:
            self.get_token_from_browser()
            while not self.url:
                sleep(.5)
            code = self.url.split("?code=")[1].split("&")[0]
            self.url = None
            token_info = self.sp_oauth.get_access_token(code)
        if token_info:
            return token_info['access_token']
        else:
            return None

    def get_token_from_browser(self):
        self.browserListenerThread = threading.Thread(target=self.listen_for_token_redirect())
        self.browserListenerThread.setDaemon(True)
        self.browserListenerThread.start()

    def listen_for_token_redirect(self):
        subprocess.call(["open", self.sp_oauth.get_authorize_url()])
        webserver = Web_Server()
        self.url = webserver.run()

    def sort(self, results, sort_field, reverse=False):
        return sorted(results, key = lambda k: k[sort_field], reverse = reverse)

    def track_search(self, searchStr, limit=50):
        tracks = self.spotify.search(searchStr, limit, type='track')
        return {
            'tracks': self.parse_tracks(tracks['tracks']['items'], source='search')
        }

    def album_search(self, searchStr, limit=10):
        albums = self.spotify.search(searchStr, limit, type='album')
        return {
            'albums': self.parse_albums(albums['albums']['items'])
        }

    def artist_search(self, searchStr, limit=5):
        artists = self.spotify.search(searchStr, limit=5, type='artist')
        return {
            'artists': self.parse_artists(artists['artists']['items'])
        }

    def full_search(self, searchStr):
        return {
            'artists': self.artist_search(searchStr)['artists'],
            'albums': self.album_search(searchStr)['albums'],
            'tracks': self.track_search(searchStr)['tracks'],
        }
    
    def get_artist(self, artist):
        albums = self.spotify.artist_albums(artist['artist_id'])
        tracks = self.spotify.artist_top_tracks(artist['artist_id'])
        return {
            'albums': self.parse_albums(albums['items']),
            'tracks': self.parse_tracks(tracks['tracks'])
        }

    def get_album(self, album):
        tracks = self.spotify.album(album['album_id'])
        return {
            'tracks': self.parse_tracks(tracks['tracks']['items'], source='album', album=album['album_name'])
        }

    def parse_tracks(self, results, artist=None, album=None, source=None):
        res = []
        for track in results:
            track_info = {
                'track_name': track['name'],
                'track_number': track['track_number'],
                'album_name': album or track['album']['name'],
                'artist_name': artist or track['artists'][0]['name'],
                'track_uri': track['uri'],
                'category': 'track',
            }
            if source == 'search':
                track_info['popularity'] = track['popularity']
            res.append(track_info)
        if source == 'search': return self.sort(res, 'popularity', reverse=True)
        elif source == 'album': return self.sort(res, 'track_number', reverse=False)
        else: return res

    def parse_albums(self,results):
        res = []
        for album in results:
            if album['images'] and len(album['images']) > 0:
                art_info = album['images'][len(album['images'])-1]
                art_image = self.asciinator(art_info['url'], .1, 1)
            else:
                art_image = None
            res.append({
                'album_id': album['id'],
                'album_name': album['name'],
                'album_uri': album['uri'],
                'album_art': art_image,
                'category': 'album',
            })
        return res

    def parse_artists(self, results):
        res = []
        for artist in results:
            res.append({
                'artist_id': artist['id'],
                'artist_name': artist['name'],
                'artist_uri': artist['uri'],
                'popularity': artist['popularity'],
                'category': 'artist',
            })
        return self.sort(res, 'popularity', reverse=True)

    # https://gist.github.com/cdiener/10491632
    def asciinator(self, url, scaling, intensity):
        chars = numpy.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
        widthCorrection = 7/4
        f = io.BytesIO(urllib.urlopen(url).read())
        img = Image.open(f)
        newsize = (round(img.size[0]*scaling*widthCorrection), round(img.size[1]*scaling))
        img = numpy.sum(numpy.asarray(img.resize(newsize)), axis=2)
        img -= img.min()
        img = (1.0 - img/img.max())**intensity*(chars.size-1)
        return ( '|'.join( ("".join(r) for r in chars[img.astype(int)] ) ) )

