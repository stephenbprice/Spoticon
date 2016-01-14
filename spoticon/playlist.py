class Playlist:

    def __init__(self):
        self.playlist = []
        self.currentPlaylistIndex = -1

    def add_track(self, track):
        self.playlist.append(track)

    def add_tracks(self, tracks):
        self.playlist += tracks

    def clear_playlist(self):
        self.playlist = []
        self.currentPlaylistIndex = -1

    def has_next_track(self):
        return self.currentPlaylistIndex < (len(self.playlist) - 1)

    def has_previous_track(self):
        return self.currentPlaylistIndex > 0 and self.currentPlaylistIndex <= len(self.playlist)

    def next_track(self):
        if self.has_next_track():
            self.currentPlaylistIndex += 1
            return self.playlist[self.currentPlaylistIndex]
        else:
            return None

    def prev_track(self):
        if self.has_previous_track():
            self.currentPlaylistIndex -= 1
            return self.playlist[self.currentPlaylistIndex]
        else:
            return None

