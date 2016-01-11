import subprocess
import time
import curses
import spotipy, json
import threading

from operator import attrgetter


class Spoticon(object):


    def __init__(self, stdScr):

        #Default curses screen
        self.stdScr = stdScr

        #Variables for general playback
        self.nowPlaying = None
        self.repeatOneSong = False
        self.pauseCount = 0

        #Initial curses setup
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.stdScr.keypad(1)

        #Variables for windows
        self.stdScrHeight, self.stdScrWidth = self.stdScr.getmaxyx()
        self.nowPlayingScrHeight = 6
        self.mainScrHeight = self.stdScrHeight - self.nowPlayingScrHeight

        #Variables for back/forward navigation
        self.results = []
        self.backHistory = []
        self.forwardHistory = []

        #Variables for playlists
        self.playlist = []
        self.currentPlaylistIndex = -1
        self.playerListenerThread = threading.Thread(target = self.listen_for_song_advance)
        self.closePlayerListener = False

        #Variables for Scrolling Screen
        self.topLineNum = 0
        self.highlightLineNum = 0

        #Soptipy object
        self.spotify = spotipy.Spotify()

        #Subscreens
        self.mainScr = self.stdScr.derwin(self.mainScrHeight, self.stdScrWidth, 0, 0)
        self.nowPlayingScr = self.stdScr.derwin(self.nowPlayingScrHeight, self.stdScrWidth, self.mainScrHeight, 0)

        self.run()


    def run(self):
        self.show_intro()
        self.start_player_listener_thread()
        self.listen_for_commands()



    def show_intro(self):
        introScreen = '''
        SPOTICON by Stephen B Price
        ''' 

        self.mainScr.addstr(1, 1, introScreen)


    def listen_for_commands(self):
        while True:
            self.display_main_screen()
            charInput = self.stdScr.getch()

            if (charInput == ord('q')):
                self.stop_player_listener_thread()
                curses.endwin()
                break
            elif (charInput == ord('s')):
                self.search_content()
            elif (charInput == ord('\n')):
                line = self.results[self.highlightLineNum]
                self.play_song(line)
            elif (charInput == ord(' ')):
                self.play_pause()
            elif (charInput == ord('j')):
                self.updown(1)
            elif (charInput == ord('k')):
                self.updown(-1)
            elif (charInput == ord('l')):
                self.forward_history();
            elif (charInput == ord('h')):
                self.back_history();
            elif (charInput == ord('r')):
                self.toggle_repeat_one_song()
            elif (charInput == ord('L')):
                self.playlist_play_next()
            elif (charInput == ord('H')):
                self.playlist_play_last()
            elif (charInput == ord('C')):
                self.clear_playlist()
            elif (charInput == ord('+')):
                line = self.results[self.highlightLineNum]
                self.add_song_to_playlist(line)
            elif (charInput == ord('A')):
                self.add_all_songs_to_playlist()

    def get_input(self, prompt):
        curses.curs_set(1)
        searchScr = self.stdScr.derwin(5, 40, 20, 20)
        searchScr.refresh()
        searchScr.addstr(0, 0, prompt)
        curses.echo()
        usrInput = searchScr.getstr().decode(encoding='utf-8')
        curses.noecho()
        curses.curs_set(0)
        searchScr.clear()
        del searchScr
        self.mainScr.refresh()
        
        return usrInput


    def search_content(self):
        searchStr = self.get_input('Search: ')

        if (len(searchStr) > 2):
            if (self.results):
                self.backHistory.append(self.results)
                self.topLineNum = 0
                self.highlightLineNum = 0
            searchResults = self.spotify.search(searchStr, limit=50)
            self.results = self.parse_spotify_results(searchResults)

        if(self.results):
            self.display_main_screen()

    
    def forward_history(self):
        if(self.forwardHistory):
            self.backHistory.append(self.results)
            self.results = self.forwardHistory.pop()
            self.display_main_screen()


    def back_history(self):
        if (self.backHistory):
            self.forwardHistory.append(self.results)
            self.results = self.backHistory.pop()
            self.display_main_screen()


    def toggle_repeat_one_song(self):
        self.repeatOneSong = not self.repeatOneSong


    def add_song_to_playlist(self, song):
        self.playlist.append(song)
    

    def add_all_songs_to_playlist(self):
        if self.results:
            self.playlist += self.results
        
    def clear_playlist(self):
        self.playlist = []
        self.currentPlaylistIndex = -1


    def playlist_play_next(self):
        if (self.currentPlaylistIndex < len(self.playlist) - 1):
            self.currentPlaylistIndex += 1
            self.play_song(self.playlist[self.currentPlaylistIndex])

    def playlist_play_last(self):
        if(self.currentPlaylistIndex > 0 and self.currentPlaylistIndex < len(self.playlist)):
            self.currentPlaylistIndex -= 1
            self.play_song(self.playlist[self.currentPlaylistIndex])
    
    #Scrolling code pulled from Lyle Scott's Python-curses-Scrolling-Example
    #https://github.com/LyleScott/Python-curses-Scrolling-Example/
    def display_main_screen(self):
        self.mainScr.erase()
        top = self.topLineNum
        bottom = self.topLineNum + self.mainScrHeight
        for (index,line,) in enumerate(self.results[top:bottom]):
            linenum = self.topLineNum + index
            lineString = self.format_line(line)

            if index != self.highlightLineNum:
                self.mainScr.addstr(index, 0, lineString)
            else:
                self.mainScr.addstr(index, 0, lineString, curses.A_BOLD)
        self.mainScr.refresh()

    def updown(self, increment):
        nextLineNum = self.highlightLineNum + increment

        #Paging
        if increment == -1 and self.highlightLineNum == 0 and self.topLineNum != 0:
            self.topLineNum -= 1
            return
        elif increment == 1 and nextLineNum == self.mainScrHeight and (self.topLineNum + self.mainScrHeight) != len(self.results):
            self.topLineNum += 1
            return

        #Scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum + self.highlightLineNum + 1) != len(self.results) and self.highlightLineNum != len(self.results):
            self.highlightLineNum = nextLineNum


    def format_line(self, line):
        return '{0:<45} {1:^25} {2:>25}'.format(line.get('song_name')[:30], line.get('album_name')[:20], line.get('artist_name')[:20])

        
    def parse_spotify_results(self, results):
        res = []
        for track in results['tracks']['items']:
            song_name = track['name']
            album_name = track['album']['name']
            artist_name = track['artists'][0]['name']
            song_uri = track['uri']
            popularity = track['popularity']
            res.append({'song_name': song_name, 'album_name': album_name, 'artist_name': artist_name, 'song_uri': song_uri, 'popularity': popularity})
        return self.sort_results(res)

    
    def sort_results(self, results):
        return sorted(results, key = lambda k: k['popularity'], reverse = True)


    def start_player_listener_thread(self):
        self.playerListenerThread.setDaemon(True)
        self.playerListenerThread.start()


    def stop_player_listener_thread(self):
        self.closePlayerListener = True


    def listen_for_song_advance(self):
        while not self.closePlayerListener:
            playerState = self.get_player_state()
            playerPosition = self.get_player_position()
            if (playerState == 'paused' or playerState == 'stopped') and playerPosition == '0.0':
                if self.nowPlaying and self.repeatOneSong:
                    self.play_song(self.nowPlaying)
                elif self.playlist:
                    if self.pauseCount >= 2:
                        self.playlist_play_next()
                        self.pauseCount = 0
                    else:
                        self.pauseCount += 1
            else:
                self.pauseCount = 0
            time.sleep(0.5)


    def play_song(self, song):
        self.nowPlaying = song
        appleScript = ['osascript', '-e', 'tell application "Spotify" to play track "{0}"'.format(song.get('song_uri'))]
        subprocess.call(appleScript)

    def play_pause(self):
        appleScript = ['osascript', '-e', 'tell application "Spotify" to playpause']
        subprocess.call(appleScript)
    
    def get_player_state(self):
        appleScript = ['osascript', '-e', 'tell application "Spotify" \n get player state \n end tell']
        playerState = subprocess.check_output(appleScript)
        return self.bytes_to_string(playerState)

    def get_player_position(self):
        appleScript = ['osascript', '-e', 'tell application "Spotify" \n get player position \n end tell']
        playerPosition = subprocess.check_output(appleScript)
        return self.bytes_to_string(playerPosition)


    def bytes_to_string(self, b):
        convertedString = b.decode('utf-8').rstrip()
        return convertedString



def run():
    curses.wrapper(Spoticon)
