import sys
import spotipy
import spotipy.oauth2 as oauth2
import threading
import subprocess

from webserver import Web_Server
from functools import reduce

class Spotify_Model(object):
    
    def __init__(self, auth, scope='playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private'):
        self.username = auth['username']
        self.client_id = auth['client_id']
        self.client_secret = auth['client_secret']
        self.redirect_uri = auth['redirect_uri']
        self.scope = scope
        self.sp_oauth = None
        self.url = None

        self.accessToken = self.get_access_token()
        if self.accessToken:
            self.spotify = spotipy.Spotify(auth=self.accessToken)
        else:
            self.spotify = spotipy.Spotify()

    def set_sp_oauth(self):
        self.sp_oauth = oauth2.SpotifyOAuth(self.client_id, self.client_secret, self.redirect_uri, scope=self.scope, cache_path=".cache-"+self.username)

    def get_access_token(self):
        if self.username and self.client_id and self.client_secret and self.redirect_uri:
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

    def get_my_playlists(self):
        playlists = self.spotify.user_playlists(self.username) if self.accessToken else None
        return {
            'playlists': self.parse_playlists(playlists)
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

    def get_playlist(self, playlist):
        tracks = self.spotify.user_playlist(playlist['owner_id'], playlist['playlist_id'])
        return {
            'tracks': self.parse_playlist(tracks['tracks']['items'])
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
            res.append({
                'album_id': album['id'],
                'album_name': album['name'],
                'album_uri': album['uri'],
                'album_art_uri': reduce(lambda f,s: f if f['height']>s['height'] else s, album['images']) if album['images'] and len(album['images']) > 0 else None,
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

    def parse_playlists(self, results):
        res = []
        if results and 'items' in results:
            for playlist in results['items']:
                res.append({
                    'playlist_name': playlist['name'],
                    'playlist_id': playlist['id'],
                    'owner_id': playlist['owner']['id'],
                    'category': 'playlist',
                })
        return res

    def parse_playlist(self, results):
        res = []
        for track in results:
            res.append({
                'track_name': track['track']['name'],
                'track_number': track['track']['track_number'],
                'album_name': track['track']['album']['name'],
                'artist_name': track['track']['artists'][0]['name'],
                'track_uri': track['track']['uri'],
                'category': 'track',
            })
        return res
