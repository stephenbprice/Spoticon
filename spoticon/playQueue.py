class PlayQueue:

    def __init__(self):
        """ Set up an internal queue for creating user playlists """

        self.playQueue = []
        self.currentPlayQueueIndex = -1

    def add_track(self, track):
        """ Add track to queue """

        self.playQueue.append(track)

    def add_tracks(self, tracks):
        """ Add array of tracks to queue """

        self.playQueue += tracks

    def clear_playQueue(self):
        """ Remove all tracks from queue """

        self.playQueue = []
        self.currentPlayQueueIndex = -1

    def has_next_track(self):
        """ Return whether queue has a next track """

        return self.currentPlayQueueIndex < (len(self.playQueue) - 1)

    def has_previous_track(self):
        """ Return whether queue has a previous track """

        return self.currentPlayQueueIndex > 0 and self.currentPlayQueueIndex <= len(self.playQueue)

    def next_track(self):
        """ Return next track in queue if next track exists """

        if self.has_next_track():
            self.currentPlayQueueIndex += 1
            return self.playQueue[self.currentPlayQueueIndex]
        else:
            return None

    def prev_track(self):
        """ Return previous track in queue if previous track exists """

        if self.has_previous_track():
            self.currentPlayQueueIndex -= 1
            return self.playQueue[self.currentPlayQueueIndex]
        else:
            return None

