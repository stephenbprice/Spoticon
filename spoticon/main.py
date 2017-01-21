import sys
import curses
import threading, time
import os.path as path

from playQueue import PlayQueue
from screens import Results_Window, Now_Playing_Window, Help_Window, Input_Window, Message_Window
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
            ord('?'): self.toggle_helpWindow,
            curses.KEY_RESIZE: self.resize_windows,
        }

        self.config = self.parse_rc()

        self.playQueue = PlayQueue()
        self.spotifyPlayer = Spotify_Player()
        self.spotifyModel = Spotify_Model(auth=self.config['auth'])

        self.stdScreen = stdScreen
        self.resize_windows()
        self.resultsWindow = Results_Window(self.stdScreen, self.resultsWindowHeight, self.resultsWindowWidth, self.resultsWindowY, self.resultsWindowX)
        self.nowplayingWindow = Now_Playing_Window(self.stdScreen, self.nowplayingWindowHeight, self.nowplayingWindowWidth, self.nowplayingWindowY, self.nowplayingWindowX)
        self.helpWindow = Help_Window(self.stdScreen, self.helpWindowHeight, self.helpWindowWidth, self.helpWindowY, self.helpWindowX)

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdScreen.keypad(1)

        self.nowPlaying = None
        self.repeatOneSong = False
        self.results = []
        self.backHistory = []
        self.forwardHistory = []

        # Thread to listen for track change
        self.playerListenerThread = threading.Thread(target=self.listen_for_track_advance)
        self.playerListenerThread.setDaemon(True)
        self.playerListenerThread.start()
        self.pauseCount = 0

        self.helpWindow.draw_screen()
        self.listen_for_commands()

    def listen_for_commands(self):
        """ Listen and interpret user commands """
        while True:
            charInput = self.stdScreen.getch()
            if charInput in self.commands:
                self.commands[charInput]()
            elif charInput == 27:
                self.quit()
                break

    def resize_windows(self):
        """ Ensure Curses screen size """
        height, width = self.stdScreen.getmaxyx()
        if height < 40 or width < 100:
            self.quit('Spoticon cannot run with a screen resolution of 25x100. Please resize the window and restart Spoticon.');
        else:
            self.nowplayingWindowHeight = 5
            self.nowplayingWindowWidth = width
            self.nowplayingWindowX = 0
            self.nowplayingWindowY = height - 5

            self.resultsWindowHeight = height - 5
            self.resultsWindowWidth = width
            self.resultsWindowX = 0
            self.resultsWindowY = 0

            self.inputWindowHeight = 3
            self.inputWindowWidth = int(width * .66)
            self.inputWindowX = int(width * .16)
            self.inputWindowY = int(height * .5) - 1

            self.messageWindowHeight = 3
            self.messageWindowWidth = int(width * .5)
            self.messageWindowX = int(width * .25)
            self.messageWindowY = int(height * .66) - 1

            self.helpWindowHeight = int(height * .66)
            self.helpWindowWidth = int(width * .66)
            self.helpWindowX = int(width * .16)
            self.helpWindowY = int(height * .16)

    def refresh_windows(self):
        if self.resultsWindow: self.resultsWindow.draw_screen()
        if self.nowplayingWindow: self.nowplayingWindow.draw_screen()
        if self.helpWindow: self.helpWindow.draw_screen()

    def listen_for_track_advance(self):
        """ Listen for Spotify Player state """
        playerState = self.spotifyPlayer.get_player_state()
        playerPosition = self.spotifyPlayer.get_player_position()
        if (playerState == 'paused' or playerState == 'stopped') and playerPosition == '0.0':
            if self.nowPlaying and self.repeatOneSong:
                self.play_track(self.nowPlaying)
            elif self.pauseCount > 2:
                self.playQueue_play_next()
            else:
                self.pauseCount += 1
        else:
            self.pauseCount = 0
        time.sleep(.5)

    def update(self, results):
        """ Add curent results to backHistory replace with new results
            Args:
                results (obj) = The new results to display
        """
        if self.helpWindow:
            del self.helpWindow.win
            self.helpWindow = None
        if self.results:
            self.backHistory.append(self.results)
        self.results = results
        self.resultsWindow.draw_screen(lines=self.results)
        self.nowplayingWindow.draw_screen()

    def search(self):
        """ Get user input from search screen, query Spotify API, and update results """
        inputWindow = Input_Window(self.stdScreen, self.inputWindowHeight, self.inputWindowWidth, self.inputWindowY, self.inputWindowX)
        query = inputWindow.get_user_input('SEARCH: ')

        if len(query) > 2:
            if self.helpWindow:
                del self.helpWindow.win
                self.helpWindow = None
            results = self.spotifyModel.full_search(query)
            self.update(results)
        else:
            self.refresh_windows()

    def open_artist(self, artist):
        """ Get and update results with tracks/albums from artist
            Args:
                artist (obj) = An artist object
        """
        if artist and 'artist_id' in artist:
            self.update(self.spotifyModel.get_artist(artist['artist_id']))

    def get_track_album(self):
        """ Open album of track """
        self.open_album(self.resultsWindow.get_highlighted_line())

    def get_track_artist(self):
        """ Open artist results for track artist """
        self.open_artist(self.resultsWindow.get_highlighted_line())

    def open_album(self, item):
        """ Get and update results with tracks from album
            Args:
                item (obj) = An spotify result object
        """
        if item and 'album_id' in item:
            name = item['album_name'] if 'album_name' in item else ''
            self.update(self.spotifyModel.get_album(item['album_id'], album_name=name))
        else:
            self.flash_message('Cannot open album', 0.5)

    def open_my_playlists(self):
        """ Search for user playlists and update results """
        self.update(self.spotifyModel.get_my_playlists())

    def open_playlist(self, playlist):
        """ Get and update results with tracks from playlist
            Args:
                playlist (obj) = The highlighted line
        """
        self.update(self.spotifyModel.get_playlist(playlist))

    def play_track(self, track):
        """ Play track

            Args:
                track (obj) = The track to play
        """
        if track and 'track_uri' in track:
            self.nowPlaying = track
            self.spotifyPlayer.play_track(track['track_uri'])
            self.nowplayingWindow.draw_screen(track=track)

    def activate_selected_line(self):
        """ Activate current highlighted line """
        line = self.resultsWindow.get_highlighted_line()
        if line and 'category' in line:
            if line['category'] == 'artist':
                self.open_artist(line)
            elif line['category'] == 'playlist':
                self.open_playlist(line)
            elif line['category'] in ['album', 'album_art']:
                album = self.resultsWindow.get_album()
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
        if not self.helpWindow:
            self.resultsWindow.updown(1)

    def move_down(self):
        """ Move highlighted screen line down """
        if not self.helpWindow:
            self.resultsWindow.updown(-1)

    def move_left(self):
        """ Move highlighted screen line left """
        if not self.helpWindow:
            self.resultsWindow.leftright(-1)

    def move_right(self):
        """ Move highlighted screen line right """
        if not self.helpWindow:
            self.resultsWindow.leftright(1)

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
        line = self.resultsWindow.get_highlighted_line()
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

    def flash_message(self, message, time):
        """ Display message in message screen
            Args:
                message (str) = Message to display
                time (float) = The time interval to display message
        """
        messageWindow = Message_Window(self.stdScreen, self.messageWindowHeight, self.messageWindowWidth, self.messageWindowY, self.messageWindowX)
        messageWindow.flash_message(message, time)
        self.refresh_windows()

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
            self.resultsWindow.draw_screen(self.results)


    def back_history(self):
        """ Display previous screen on main screen """
        if self.backHistory:
            self.forwardHistory.append(self.results)
            self.results = self.backHistory.pop()
            self.resultsWindow.draw_screen(self.results)

    def toggle_helpWindow(self):
        """ Toggle help screen """
        if self.helpWindow:
            self.helpWindow.win.clear()
            del self.helpWindow.win
            self.helpWindow = None
            self.refresh_windows()
        else:
            self.helpWindow = Help_Window(self.stdScreen, self.helpWindowHeight, self.helpWindowWidth, self.helpWindowY, self.helpWindowX)
            self.helpWindow.draw_screen()

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

    def quit(self, message=''):
        """ Gracefully quit program """
        curses.endwin()
        if message: print(message)
        sys.exit()


def run():
    """ Call Spoticon class with automatically passed curses object """

    curses.wrapper(Spoticon)
