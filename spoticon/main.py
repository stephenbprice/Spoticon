import sys
import curses
import threading, time
import os.path as path

from playQueue import PlayQueue
from screens import Search_Screen, Now_Playing_Screen, Input_Screen, Message_Screen
from spotifyModel import Spotify_Model
from spotifyPlayer import Spotify_Player
from webserver import Web_Server

class Spoticon(object):

    def __init__(self, stdScreen):
        """ Controller for Spoticon program """

        self.commands = {
            ord('s'): self.search,
            ord('\n'): self.activate_selected_line,
            ord(' '): self.play_pause,
            ord('j'): self.move_up,
            ord('k'): self.move_down,
            ord('h'): self.move_left,
            ord('l'): self.move_right,
            ord('a'): self.get_track_album,
            ord('A'): self.get_track_artist,
            ord('f'): self.forward_history,
            ord('b'): self.back_history,
            ord('r'): self.toggle_repeat_one_track,
            ord('L'): self.playQueue_play_next,
            ord('H'): self.playQueue_play_last,
            ord('C'): self.playQueue_clear_playQueue,
            ord('+'): self.playQueue_add_highlighted_track,
            ord('.'): self.playQueue_add_all_tracks,
            ord('q'): self.display_playQueue,
            ord('p'): self.open_my_playlists,
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
        self.inputScreenHeight = 3
        self.inputScreenWidth = None
        self.inputScreenX = None
        self.inputScreenY = None
        self.messageScreenHeight = 3
        self.messageScreenWidth = None
        self.messageScreenX = None
        self.messageScreenY = None
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

        # Spotipy controller
        self.spotifyModel = Spotify_Model(auth=self.config['auth'])

        self.curses_screen_setup();
        self.listen_for_commands()

    def curses_screen_setup(self):
        """ Set up curses screens on init and resize """

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

            self.inputScreenWidth = self.messageScreenWidth = int(self.stdScreenWidth / 2)
            self.inputScreenX = self.messageScreenX = int(self.stdScreenWidth / 4)
            self.inputScreenY = int(self.stdScreenHeight / 2) - 1
            self.messageScreenY = int (self.stdScreenHeight * .66)

    def listen_for_commands(self):
        """ Listen and interpret user commands """

        while True:
            if self.results:
                self.searchScreen.draw_screen(self.results)
            charInput = self.stdScreen.getch()
            if charInput in self.commands:
                self.commands[charInput]()
            elif charInput == 27:
                self.quit()
                break

    def parse_rc(self):
        """ Return parsed .spoticonrc file if one exists """

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
        """ Start thread listening to Spotify Player state """
      
        self.playerListenerThread.setDaemon(True)
        self.playerListenerThread.start()

    def stop_player_listener_thread(self):
        """ Stop thread listening to Spotify Player state """

        self.closePlayerListener = True

    def listen_for_track_advance(self):
        """ Listen for Spotify Player state """

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
        """ Gracefully quit program """

        self.stop_player_listener_thread()
        curses.endwin()
        print('quitting')
        if message: print(message)
        sys.exit()

    def update(self, results):
        """ Add curent results to backHistory replace with new results

            Args:
                results (obj) = The new results to display
        """

        if self.results:
            self.backHistory.append(self.results)
        self.results = results
        self.searchScreen.draw_screen(self.results)

    def search(self):
        """ Get user input from search screen, query Spotify API, and update results """

        searchStr = self.get_input('Search: ')

        if len(searchStr) > 2:
            results = self.spotifyModel.full_search(searchStr)
            self.update(results)

    def open_artist(self, artist):
        """ Get and update results with tracks/albums from artist

            Args:
                artist (obj) = An artist object
        """

        if 'artist_id' in artist:
            results = self.spotifyModel.get_artist(artist['artist_id'])
            self.update(results)

    def get_track_album(self):
        """ Open album of track """

        line = self.searchScreen.get_highlighted_line()
        self.open_album(line)

    def get_track_artist(self):
        """ Open artist results for track artist """

        line = self.searchScreen.get_highlighted_line()
        self.open_artist(line)

    def open_album(self, item):
        """ Get and update results with tracks from album

            Args:
                item (obj) = An spotify result object
        """

        if 'album_id' in item:
            name = item['album_name'] if 'album_name' in item else ''
            results = self.spotifyModel.get_album(item['album_id'], album_name=name)
            self.update(results)
        else:
            self.flash_message('Cannot open album', 0.5)

    def open_my_playlists(self):
        """ Search for user playlists and update results """

        results = self.spotifyModel.get_my_playlists()
        self.update(results)

    def open_playlist(self, playlist):
        """ Get and update results with tracks from playlist

            Args:
                playlist (obj) = The highlighted line
        """

        if 'playlist_id' in playlist:
            results = self.spotifyModel.get_playlist(playlist['playlist_id'])
            self.update(results)

    def play_track(self, track):
        """ Play track

            Args:
                track (obj) = The track to play
        """

        if 'track_uri' in track:
            self.nowPlaying = track
            self.spotifyPlayer.play_track(track['track_uri'])
            self.nowPlayingScreen.draw_screen(track)

    def activate_selected_line(self):
        """ Activate current highlighted line """

        if self.searchScreen.results:
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
        """ Toggle Spotify Player play/pause """

        self.spotifyPlayer.play_pause()
        self.flash_message('Play/Pause Spotify Player', 0.5)

    def move_up(self):
        """ Move highlighted screen line up """

        self.searchScreen.updown(1)

    def move_down(self):
        """ Move highlighted screen line down """

        self.searchScreen.updown(-1)

    def move_left(self):
        """ Move highlighted screen line left """

        self.searchScreen.leftright(-1)

    def move_right(self):
        """ Move highlighted screen line right """

        self.searchScreen.leftright(1)

    def toggle_repeat_one_track(self):
        """ Toggle switch to repeat the same one song endlessly """

        self.repeatOneSong = not self.repeatOneSong

    def playQueue_play_next(self):
        """ Play next song in the Spoticon queue """

        if self.playQueue.has_next_track():
            track = self.playQueue.next_track()
            self.play_track(track)

    def playQueue_play_last(self):
        """ Play previous song in the Spoticon queue """

        if self.playQueue.has_previous_track():
            track = self.playQueue.prev_track()
            self.play_track(track)

    def playQueue_clear_playQueue(self):
        """ Remove all tracks form the Spoticon queue """

        self.playQueue.clear_playQueue()

    def playQueue_add_highlighted_track(self):
        """ Add current line item track to the Spoticon queue """

        line = self.searchScreen.get_highlighted_line()
        if line['category'] == 'track':
            self.playQueue.add_track(line)

    def playQueue_add_all_tracks(self):
        """ Add all tracks on screen to the Spoticon queue """

        self.playQueue.add_tracks(self.results['tracks'])

    def display_playQueue(self):
        """ Show tracks in Spoticon queue on screen """

        results = {}
        results['tracks'] = self.playQueue.playQueue
        self.update(results)

    def get_input(self, prompt):
        """ Display input screen with prompt message and return user input

            Args:
                prompt (str) = The prompt string to display
        """

        inputScreen = Input_Screen(self.stdScreen, self.inputScreenHeight, self.inputScreenWidth, self.inputScreenY, self.inputScreenX)
        usrInput = inputScreen.get_user_input(prompt)
        self.searchScreen.refresh()
        return usrInput

    def flash_message(self, message, time):
        """ Display message in message screen

            Args:
                message (str) = Message to display
                time (float) = The time interval to display message
        """

        messageScreen = Message_Screen(self.stdScreen, self.messageScreenHeight, self.messageScreenWidth, self.messageScreenY, self.messageScreenX)
        messageScreen.flash_message(message, time)

    def set_now_playing_scr(self):
        """ Set text and styize the now playing screen """

        nowPlayingString = self.spotifyPlayer.get_now_playing_str()
        self.nowPlayingScreen.clear()
        self.nowPlayingScreen.border(1)
        self.nowPlayingScreen.addstr(2, 5, nowPlayingString)
        self.nowPlayingScreen.refresh()

    def forward_history(self):
        """ Display next step in forward history on main screen """

        if self.forwardHistory:
            self.backHistory.append(self.results)
            self.results = self.forwardHistory.pop()
            self.searchScreen.draw_screen(self.results)


    def back_history(self):
        """ Display previous screen on main screen """

        if self.backHistory:
            self.forwardHistory.append(self.results)
            self.results = self.backHistory.pop()
            self.searchScreen.draw_screen(self.results)


def run():
    """ Call Spoticon class with automatically passed curses object """

    curses.wrapper(Spoticon)
