import sys
import spotipy
import spotipy.oauth2 as oauth2
import threading
import subprocess

from webserver import Web_Server
from functools import reduce

class Spotify_Model(object):
    
    def __init__(self, auth, scope='playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private'):
        """ A controller to communicate with Spotipy

            Args:
                auth (obj) = An object containing the auth creds for the Spotify API
                username (str) = Spotify username
                clint_id (str) = Spotify client id
                client_secret (str) = Spotify client secret
                redirect_uri (str) = Spotify app redirect uri
        """

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
        """ Set up spotipy Oauth2 authorization """

        self.sp_oauth = oauth2.SpotifyOAuth(self.client_id, self.client_secret, self.redirect_uri, scope=self.scope, cache_path=".cache-"+self.username)

    def get_access_token(self):
        """ Return Spotify Web API authorization access token """

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
        """ Start thread to listen for spotify redirect to localhost with authorization code """

        self.browserListenerThread = threading.Thread(target=self.listen_for_token_redirect())
        self.browserListenerThread.setDaemon(True)
        self.browserListenerThread.start()

    def listen_for_token_redirect(self):
        """ Start web server to get authorization code on spotify redirect to localhost """

        subprocess.call(["open", self.sp_oauth.get_authorize_url()])
        webserver = Web_Server()
        self.url = webserver.run()

    def search(self, method, *args, **kwargs):
        """ Refresh expired access token if required and return results from spotipy method

            Args:
                method (func) = The spotipy method to execute
        """

        self.access_token = self.get_access_token()
        if self.access_token:
            self.spotify._auth = self.access_token
        return method(*args, **kwargs)

    def sort(self, results, sort_field, reverse=False):
        """ Return sorted results

            Args:
                results (array) = The results to sort
                sort_field (str) = The name of the field to sort by
                reverse (boolean) = Whether to reverse sort
        """

        return sorted(results, key = lambda k: k[sort_field], reverse = reverse)

    def track_search(self, query, limit=50):
        """ Return tracks matching query 

            Args:
                query (str) = The string
                limit (int) = The max number of results
        """

        tracks = self.search(self.spotify.search, query, limit, type='track')
        return {
            'tracks': self.parse_tracks(tracks['tracks']['items'], source='search')
        }

    def album_search(self, query, limit=10):
        """ Return albumss matching query 

            Args:
                query (str) = The query string
                limit (int) = The max number of results
        """

        albums = self.search(self.spotify.search, query, limit, type='album')
        return {
            'albums': self.parse_albums(albums['albums']['items'])
        }

    def artist_search(self, query, limit=5):
        """ Return artists matching query 

            Args:
                query (str) = The query string
                limit (int) = The max number of results
        """

        artists = self.search(self.spotify.search, query, limit=5, type='artist')
        return {
            'artists': self.parse_artists(artists['artists']['items'])
        }

    def get_my_playlists(self):
        """ Return user playlists """

        playlists = self.search(self.spotify.user_playlists, self.username) if self.accessToken else None
        return {
            'playlists': self.parse_playlists(playlists)
        }

    def full_search(self, query):
        """ Return artists, albums, and tracks matching query

            Args:
                query (str) = The query string
        """

        return {
            'artists': self.artist_search(query)['artists'],
            'albums': self.album_search(query)['albums'],
            'tracks': self.track_search(query)['tracks'],
        }
    
    def get_artist(self, artist_id):
        """ Return albums and tracks for artist

            Args:
                artist_id (str) = The Spotify artist_id for the artist to get results for
        """

        albums = self.search(self.spotify.artist_albums, artist_id)
        tracks = self.search(self.spotify.artist_top_tracks, artist_id)
        return {
            'albums': self.parse_albums(albums['items']),
            'tracks': self.parse_tracks(tracks['tracks'])
        }

    def get_album(self, album):
        """ Return tracks for album

            Args:
                artist (str) = The album object to get tracks for 
        """

        tracks = self.search(self.spotify.album, album['album_id'])
        return {
            'tracks': self.parse_tracks(tracks['tracks']['items'], source='album', album=album['album_name'])
        }

    def get_playlist(self, playlist_id):
        """ Return tracks for playlist_id

            Args:
                playlist_id (str) = The Spotify playlist_id to get tracks for
        """

        tracks = self.search(self.spotify.user_playlist, playlist['owner_id'], playlist['playlist_id'])
        return {
            'tracks': self.parse_playlist(tracks['tracks']['items'])
        }

    def parse_tracks(self, results, artist=None, album=None, source=None):
        """ Return track results in a better format

            Args:
                results (array) = Results of a Spotify API query for tracks
                artist (str) = The track results' artist
                album (str) = The track results' album
                source (str) = The type of search the results came from. This is necessary
                               because Spotify does not always return tracks from different
                               types of queries the same format.
        """

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

    def parse_albums(self, results):
        """ Return album results in a better format
        
            Args:
                results (array) = Results of a Spotify API query for albums
        """

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
        """ Return artist results in a better format
        
            Args:
                results (array) = Results of a Spotify API query for artists
        """

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
        """ Return playlists results in a better format
        
            Args:
                results (array) = Results of a Spotify API query for playlists
        """

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

    def parse_playlist(self, result):
        """ Return single playlist result in a better format
        
            Args:
                result (array) = Results of a Spotify API query for a single playlist
        """

        res = []
        for track in result:
            res.append({
                'track_name': track['track']['name'],
                'track_number': track['track']['track_number'],
                'album_name': track['track']['album']['name'],
                'artist_name': track['track']['artists'][0]['name'],
                'track_uri': track['track']['uri'],
                'category': 'track',
            })
        return res
