import subprocess
import curses
import spotipy, json

class Spoticon(object):


    def __init__(self, stdScr):

        self.stdScr = stdScr

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
                curses.endwin()
                break
            elif (charInput == ord('s')):
                self.search_content()
            elif (charInput == ord('\n')):
                line = self.results[self.highlightLineNum]
                self.play_song(line.get('song_uri'))
            elif (charInput == ord('j')):
                self.updown(1)
            elif (charInput == ord('k')):
                self.updown(-1)

    def get_input(self, prompt):
        curses.curs_set(1)
        searchScr = self.stdScr.derwin(20, 20, 20, 20)
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
                self.back_history.append(self.results)
            searchResults = self.spotify.search(searchStr)
            self.results = self.parse_spotify_results(searchResults)

        if(self.results):
            self.display_main_screen()


    def display_main_screen(self):
        self.mainScr.erase()
        top = self.topLineNum
        bottom = self.topLineNum + self.mainScrHeight
        for (index,line,) in enumerate(self.results):
            linenum = self.topLineNum + index
        
            if index != self.highlightLineNum:
                self.mainScr.addstr(index, 0, line.get('song_name'))
            else:
                self.mainScr.addstr(index, 0, line.get('song_name'), curses.A_BOLD)
        self.mainScr.refresh()

    def updown(self, increment):
        nextLineNum = self.highlightLineNum + increment

        #Paging
        if increment == -1 and self.highlightLineNum == 0 and self.topLineNum != 0:
            self.topLineNum -= 1
            return
        elif increment == 1 and nextLineNum == self.mainScrHeight and (self.topLineNum + self.mainScrHeight) != len(self.results):
            self.topLineNum += 1

        #Scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum + self.highlightLineNum + 1) != len(self.results) and self.highlightLineNum != len(self.results):
            self.highlightLineNum = nextLineNum


    def parse_spotify_results(self, results):
        res = []
        for track in results['tracks']['items']:
            song_name = track['name']
            song_uri = track['uri']
            res.append({'song_name': song_name, 'song_uri': song_uri})
        return res


    def play_song(self, song_uri):
        appleScript = ['osascript', '-e', 'tell application "Spotify" to play track "{0}"'.format(song_uri)]
        subprocess.call(appleScript)

def run():
    curses.wrapper(Spoticon)
