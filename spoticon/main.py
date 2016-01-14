import curses
import threading, time

from playlist import Playlist
from screens import Search_Screen, Now_Playing_Screen, Input_Screen
from spotifyModel import Spotify_Model
from spotifyPlayer import Spotify_Player

class Spoticon(object):

    def __init__(self, stdScreen):

        self.commands = {
            ord('s'): self.search,
            ord('\n'): self.play_highlighted_track,
            ord(' '): self.play_pause,
            ord('j'): self.move_up,
            ord('k'): self.move_down,
            ord('l'): self.forward_history,
            ord('h'): self.back_history,
            ord('r'): self.toggle_repeat_one_track,
            ord('L'): self.playlist_play_next,
            ord('H'): self.playlist_play_last,
            ord('C'): self.playlist_clear_playlist,
            ord('+'): self.playlist_add_highlighted_track,
            ord('A'): self.playlist_add_all_tracks,
        }

        self.playlist = Playlist()
        self.spotifyModel = Spotify_Model()
        self.spotifyPlayer = Spotify_Player()

        #Default curses screen
        self.stdScreen = stdScreen

        #Initial curses setup
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdScreen.keypad(1)

        #Variables for windows
        self.stdScreenHeight, self.stdScreenWidth = self.stdScreen.getmaxyx()
        self.nowPlayingScreenHeight = 6
        self.searchScreenHeight = self.stdScreenHeight - self.nowPlayingScreenHeight

        #Subscreens
        self.searchScreen = Search_Screen(self.stdScreen, self.searchScreenHeight, self.stdScreenWidth, 0, 0)
        self.nowPlayingScreen = Now_Playing_Screen(self.stdScreen, self.nowPlayingScreenHeight, self.stdScreenWidth, self.searchScreenHeight, 0)

        #Variables for Player Features
        self.nowPlaying = None
        self.repeatOneSong = False

        #Variables for back/forward navigation
        self.results = []
        self.backHistory = []
        self.forwardHistory = []

        #Thread to listen for track change
        self.playerListenerThread = threading.Thread(target=self.listen_for_track_advance)
        self.closePlayerListener = False
        self.pauseCount = 0
        self.start_player_listener_thread()

        self.listen_for_commands()

    def listen_for_commands(self):
        while True:
            self.searchScreen.draw_screen(self.results)
            charInput = self.stdScreen.getch()
            if charInput in self.commands :
                self.commands[charInput]()
            elif charInput == ord('q'):
                self.quit()
                break

    def start_player_listener_thread(self):
        self.playerListenerThread.setDaemon(True)
        self.playerListenerThread.start()

    def stop_player_listener_thread(self):
        self.closePlayerListener = True

    def listen_for_track_advance(self):
        while not self.closePlayerListener:
            playerState = self.spotifyPlayer.get_player_state()
            playerPosition = self.spotifyPlayer.get_player_position()
            if (playerState == 'paused' or playerState == 'stopped') and playerPosition == '0.0':
                if self.nowPlaying and self.repeatOneSong:
                    self.play_track(self.nowPlaying)
                elif self.playlist.has_next_track():
                    if self.pauseCount >= 2:
                        self.play_track(self.playlist.next_track)
                        self.pauseCount = 0
                    else:
                        self.pauseCount += 1
            else:
                self.pauseCount = 0
            time.sleep(.5)

    def quit(self):
        print('quitting')
        self.stop_player_listener_thread()
        curses.endwin()

    def search(self):
        searchStr = self.get_input('Search: ')

        if (len(searchStr) > 2):
            if (self.results):
                self.backHistory.append(self.results)
                self.topLineNum = 0
                self.highlightLineNum = 0
            self.results = self.spotifyModel.track_search(searchStr)
            self.searchScreen.draw_screen(self.results)

    def play_track(self, track):
        self.nowPlaying = track
        self.spotifyPlayer.play_track(track)
        self.nowPlayingScreen.draw_screen(track)

    def play_highlighted_track(self):
        track = self.searchScreen.get_highlighted_track()
        self.play_track(track)

    def play_pause(self):
        self.spotifyPlayer.play_pause()

    def move_up(self):
        self.searchScreen.updown(1)

    def move_down(self):
        self.searchScreen.updown(-1)

    def toggle_repeat_one_track(self):
        self.spotifyPlayer.toggle_repeat_one_track()

    def playlist_play_next(self):
        track = self.playlist.next_track()
        self.play_track(track)

    def playlist_play_last(self):
        track = self.playlist.prev_track()
        self.play_track(track)

    def playlist_clear_playlist(self):
        self.playlist.clear_playlist()

    def playlist_add_highlighted_track(self):
        track = self.searchScreen.get_highlighted_track()
        self.playlist.add_track(track)

    def playlist_add_all_tracks(self):
        self.playlist.add_tracks(self.results)

    def get_input(self, prompt):
        inputScreen = Input_Screen(self.stdScreen, 3, 60, 20, 20)
        usrInput = inputScreen.get_user_input(prompt)
        self.searchScreen.refresh()
        return usrInput

    def set_now_playing_scr(self):
        nowPlayingString = self.spotifyPlayer.get_now_playing_str()
        self.nowPlayingScreen.clear()
        self.nowPlayingScreen.border(1)
        self.nowPlayingScreen.addstr(2, 5, nowPlayingString)
        self.nowPlayingScreen.refresh()

    def forward_history(self):
        if(self.forwardHistory):
            self.backHistory.append(self.results)
            self.results = self.forwardHistory.pop()
            self.searchScreen.draw_screen(self.results)


    def back_history(self):
        if (self.backHistory):
            self.forwardHistory.append(self.results)
            self.results = self.backHistory.pop()
            self.searchScreen.draw_screen(self.results)


def run():
    curses.wrapper(Spoticon)
