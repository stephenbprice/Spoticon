import sys
import curses
import threading, time
import os.path as path

from playQueue import PlayQueue
from screens import Search_Screen, Now_Playing_Screen, Input_Screen
from spotifyModel import Spotify_Model
from spotifyPlayer import Spotify_Player
from webserver import Web_Server

class Spoticon(object):

    def __init__(self, stdScreen):

        self.commands = {
            ord('s'): self.search,
            ord('\n'): self.activate_selected_line,
            ord(' '): self.play_pause,
            ord('j'): self.move_up,
            ord('k'): self.move_down,
            ord('h'): self.move_left,
            ord('l'): self.move_right,
            ord('f'): self.forward_history,
            ord('b'): self.back_history,
            ord('r'): self.toggle_repeat_one_track,
            ord('L'): self.playQueue_play_next,
            ord('H'): self.playQueue_play_last,
            ord('C'): self.playQueue_clear_playQueue,
            ord('+'): self.playQueue_add_highlighted_track,
            ord('A'): self.playQueue_add_all_tracks,
            ord('p'): self.open_my_playlists,
            ord('q'): self.display_playQueue,
            curses.KEY_RESIZE: self.curses_screen_setup,
        }

        # Internal playlist
        self.playQueue = PlayQueue()

        # Spotify player controller 
        self.spotifyPlayer = Spotify_Player()

        # Curses screens
        self.stdScreen = stdScreen
        self.searchScreen = None
        self.nowPlayingScreen = None
        self.stdScreenHeight = None
        self.stdScreenWidth= None
        self.searchScreenHeight = None
        self.nowPlayingScreenHeight = None
        self.curses_screen_setup()

        # Variables for player features
        self.nowPlaying = None
        self.repeatOneSong = False

        # Variables for back/forward navigation
        self.results = []
        self.backHistory = []
        self.forwardHistory = []

        # Thread to listen for track change
        self.playerListenerThread = threading.Thread(target=self.listen_for_track_advance)
        self.closePlayerListener = False
        self.pauseCount = 0
        self.start_player_listener_thread()

        # Parse spoticonrc file
        self.config = self.parse_rc()

        self.spotifyModel = Spotify_Model(auth=self.config['auth'])


        self.curses_screen_setup();
        self.listen_for_commands()

    def curses_screen_setup(self):
        # Initial curses setup
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdScreen.keypad(1)

        self.stdScreenHeight, self.stdScreenWidth = self.stdScreen.getmaxyx()
        
        if self.stdScreenHeight < 20 or self.stdScreenWidth < 100:
            self.quit('Spoticon cannot run with a screen resolution of 100x20. Please resize the window and restart Spoticon.');
        else:
            self.nowPlayingScreenHeight = 6
            self.searchScreenHeight = self.stdScreenHeight - self.nowPlayingScreenHeight

            self.searchScreen = Search_Screen(self.stdScreen, self.searchScreenHeight, self.stdScreenWidth, 0, 0)
            self.nowPlayingScreen = Now_Playing_Screen(self.stdScreen, self.nowPlayingScreenHeight, self.stdScreenWidth, self.searchScreenHeight, 0)

    def listen_for_commands(self):
        while True:
            self.searchScreen.draw_screen(self.results)
            charInput = self.stdScreen.getch()
            if charInput in self.commands:
                self.commands[charInput]()
            elif charInput == 27:
                self.quit()
                break

    def parse_rc(self):
        defaultAuth = { 
            'username': None,
            'client_id': None,
            'client_secret': None,
            'redirect_uri': None 
        }
        config = { 'auth': defaultAuth }
        try:
            with open(path.expanduser("~/.spoticonrc")) as rc:
                lines = rc.readlines()
                for line in lines:
                    words = line.split(' ')
                    if words[0] == 'username':
                        config['auth']['username'] = words[1].strip('\n')
                    elif words[0] == 'client_id':
                        config['auth']['client_id'] = words[1].strip('\n')
                    elif words[0] == 'client_secret':
                        config['auth']['client_secret'] = words[1].strip('\n')
                    elif words[0] == 'redirect_uri':
                        config['auth']['redirect_uri'] = words[1].strip('\n')
        except IOError:
            pass
        return config

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
                elif self.playQueue.has_next_track():
                    if self.pauseCount >= 2:
                        self.play_track(self.playQueue.next_track())
                        self.pauseCount = 0
                    else:
                        self.pauseCount += 1
            else:
                self.pauseCount = 0
            time.sleep(.5)

    def quit(self, message=''):
        self.stop_player_listener_thread()
        curses.endwin()
        print('quitting')
        if message: print(message)
        sys.exit()

    def update(self, results):
        if (self.results):
            self.backHistory.append(self.results)
        self.results = results
        self.searchScreen.draw_screen(self.results)

    def search(self):
        searchStr = self.get_input('Search: ')

        if (len(searchStr) > 2):
            results = self.spotifyModel.full_search(searchStr)
            self.update(results)

    def open_artist(self, line):
        results = self.spotifyModel.get_artist(line)
        self.update(results)

    def open_album(self, line):
        results = self.spotifyModel.get_album(line)
        self.update(results)

    def open_my_playlists(self):
        results = self.spotifyModel.get_my_playlists()
        self.update(results)

    def open_playlist(self, line):
        results = self.spotifyModel.get_playlist(line)
        self.update(results)

    def play_track(self, track):
        self.nowPlaying = track
        self.spotifyPlayer.play_track(track)
        self.nowPlayingScreen.draw_screen(track)

    def activate_selected_line(self):
        line = self.searchScreen.get_highlighted_line()
        if line['category'] == 'artist':
            self.open_artist(line)
        elif line['category'] == 'playlist':
            self.open_playlist(line)
        elif line['category'] in ['album', 'album_art']:
            album = self.searchScreen.get_album()
            self.open_album(album)
        elif line['category'] == 'track':
            self.play_track(line)
        else:
            pass

    def play_pause(self):
        self.spotifyPlayer.play_pause()

    def move_up(self):
        self.searchScreen.updown(1)

    def move_down(self):
        self.searchScreen.updown(-1)

    def move_left(self):
        self.searchScreen.leftright(-1)

    def move_right(self):
        self.searchScreen.leftright(1)

    def toggle_repeat_one_track(self):
        self.repeatOneSong = not self.repeatOneSong

    def playQueue_play_next(self):
        if self.playQueue.has_next_track():
            track = self.playQueue.next_track()
            self.play_track(track)

    def playQueue_play_last(self):
        if self.playQueue.has_previous_track():
            track = self.playQueue.prev_track()
            self.play_track(track)

    def playQueue_clear_playQueue(self):
        self.playQueue.clear_playQueue()

    def playQueue_add_highlighted_track(self):
        line = self.searchScreen.get_highlighted_line()
        if line['category'] == 'track':
            self.playQueue.add_track(line)

    def playQueue_add_all_tracks(self):
        self.playQueue.add_tracks(self.results['tracks'])

    def display_playQueue(self):
        results = {}
        results['tracks'] = self.playQueue.playQueue
        self.update(results)

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
        if self.forwardHistory:
            self.backHistory.append(self.results)
            self.results = self.forwardHistory.pop()
            self.searchScreen.draw_screen(self.results)


    def back_history(self):
        if self.backHistory:
            self.forwardHistory.append(self.results)
            self.results = self.backHistory.pop()
            self.searchScreen.draw_screen(self.results)


def run():
    curses.wrapper(Spoticon)
