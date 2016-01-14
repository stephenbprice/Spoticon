import spotipy

class Spotify_Model(object):
    
    def __init__(self):
        self.spotify = spotipy.Spotify()

    def parse_results(self, results):

        res = []

        for track in results['tracks']['items']:
            track_name = track['name']
            album_name = track['album']['name']
            artist_name = track['artists'][0]['name']
            track_uri = track['uri']
            popularity = track['popularity']
            res.append({'track_name': track_name, 'album_name': album_name, 'artist_name': artist_name, 'track_uri': track_uri, 'popularity': popularity})

        return self.sort_by_popularity(res)

    def sort_by_popularity(self, results):
        return sorted(results, key = lambda k: k['popularity'], reverse = True)

    def track_search(self, searchStr):
        results = self.spotify.search(searchStr, limit=50)
        return self.parse_results(results)


