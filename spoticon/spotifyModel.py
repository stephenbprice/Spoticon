import spotipy

class Spotify_Model(object):
    
    def __init__(self):
        self.spotify = spotipy.Spotify()


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
            res.append({
                'album_id': album['id'],
                'album_name': album['name'],
                'album_uri': album['uri'],
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

