class PlayQueue:

    def __init__(self):
        self.playQueue = []
        self.currentPlayQueueIndex = -1

    def add_track(self, track):
        self.playQueue.append(track)

    def add_tracks(self, tracks):
        self.playQueue += tracks

    def clear_playQueue(self):
        self.playQueue = []
        self.currentPlayQueueIndex = -1

    def has_next_track(self):
        return self.currentPlayQueueIndex < (len(self.playQueue) - 1)

    def has_previous_track(self):
        return self.currentPlayQueueIndex > 0 and self.currentPlayQueueIndex <= len(self.playQueue)

    def next_track(self):
        if self.has_next_track():
            self.currentPlayQueueIndex += 1
            return self.playQueue[self.currentPlayQueueIndex]
        else:
            return None

    def prev_track(self):
        if self.has_previous_track():
            self.currentPlayQueueIndex -= 1
            return self.playQueue[self.currentPlayQueueIndex]
        else:
            return None

