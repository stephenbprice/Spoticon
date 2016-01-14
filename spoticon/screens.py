import curses


class Search_Screen(object):

    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        #Variables for Scrolling Screen
        self.results = []
        self.topLineNum = 0
        self.highlightLineNum = 0

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)

    def refresh(self):
        self.win.refresh()

    def format_track(self, track):
        return '{0:<45} {1:^25} {2:>25}'.format(track.get('track_name')[:30], track.get('album_name')[:20], track.get('artist_name')[:20])

    def get_highlighted_track(self):
        return self.results[self.highlightLineNum]

    def draw_screen(self, results):
        if results != self.results:
            self.results = results
            self.topLineNum = 0
            self.highlightLineNum = 0

        self.win.erase()
        top = self.topLineNum
        bottom = self.topLineNum + self.height
        for (index,line,) in enumerate(results[top:bottom]):
            linenum = self.topLineNum + index
            lineString = self.format_track(line)

            if index != self.highlightLineNum:
                self.win.addstr(index, 0, lineString)
            else:
                self.win.addstr(index, 0, lineString, curses.A_BOLD)
        self.win.refresh()

    def updown(self, increment):
        nextLineNum = self.highlightLineNum + increment

        #Paging
        if increment == -1 and self.highlightLineNum == 0 and self.topLineNum != 0:
            self.topLineNum -= 1
            return
        elif increment == 1 and nextLineNum == self.height and (self.topLineNum + self.height) != len(self.results):
            self.topLineNum += 1
            return

        #Scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum + self.highlightLineNum + 1) != len(self.results) and self.highlightLineNum != len(self.results):
            self.highlightLineNum = nextLineNum


class Now_Playing_Screen(object):

    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        
        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)
        self.win.border(1)

    def format_now_playing(self, track):
        return ' {0}   -   {1}'.format(track.get('track_name'), track.get('artist_name'))

    def draw_screen(self, track):
        self.win.clear()
        self.win.addstr(1, 5, self.format_now_playing(track))
        self.win.border(1)
        self.win.refresh()

class Input_Screen(object):
    
    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):

        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)
        self.win.border(1)

    def get_user_input(self, displayMsg):
        self.win.addstr(1, 5, displayMsg)
        curses.curs_set(1)
        curses.echo()
        usrInput = self.win.getstr().decode(encoding='utf-8')
        curses.noecho()
        curses.curs_set(0)
        self.win.clear()
        del self.win

        return usrInput

