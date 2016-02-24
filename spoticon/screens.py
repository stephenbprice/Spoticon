import curses
import pdb
import math


class Search_Screen(object):

    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        #Variables for Scrolling Screen
        self.results = []
        self.formattedResults = []
        self.topLineNum = 0
        self.highlightLineNum = 0

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)

    def refresh(self):
        self.win.refresh()

    def format_album_results(self, albums):
        res = []
        for album in albums:
            for albumArtLine in range(30):
                artLine = album.get('album_art')[albumArtLine] if len(album.get('album_art')) > albumArtLine else ''
                res.append({
                    'category': 'album_art',
                    'art': artLine,
                })
            res.append(album)
        return res

    def format_line(self, line):
        if line['category'] == 'track':
            return self.format_track(line)
        elif line['category'] == 'album_art':
            return self.format_album_art(line)
        elif line['category'] == 'album':
            return self.format_album(line)
        elif line['category'] == 'artist':
            return self.format_artist(line)
        elif line['category'] == 'title_bar':
            return self.format_title_bar(line)
        else:
            return ''

    def format_track(self, track):
        return '{0:<5} {1:<45} {2:^25} {3:>25}'.format(track.get('track_number'), track.get('track_name')[:30], track.get('album_name')[:20], track.get('artist_name')[:20])

    def format_album_art(self, line):
        return '{0:<103}'.format(line.get('art')[:100])

    def format_album(self, line):
        return '{0:<103}'.format(line.get('album_name')[:100])

    def format_artist(self, artist):
        return '{0:<103}'.format(artist.get('artist_name')[:50])

    def format_title_bar(self, title_bar):
        return '{0:<103}'.format(title_bar.get('title'))

    def get_highlighted_line(self):
        return self.formattedResults[self.highlightLineNum]

    def format_results(self):
        self.formattedResults = []

        if 'artists' in self.results:
            self.formattedResults.append({
                'title': 'ARTISTS',
                'category': 'title_bar',
            })
            self.formattedResults += self.results['artists']
        if 'albums' in self.results:
            self.formattedResults.append({
                'title': 'ALBUMS',
                'category': 'title_bar',
            })
            self.formattedResults += self.format_album_results(self.results['albums'])
        if 'tracks' in self.results:
            self.formattedResults.append({
                'title': 'TRACKS',
                'category': 'title_bar',
            })
            self.formattedResults += self.results['tracks']

    def draw_screen(self, results):
        if results != self.results:
            self.results = results
            self.format_results()
            self.topLineNum = 0
            self.highlightLineNum = 0

        self.win.erase()
        top = self.topLineNum
        bottom = self.topLineNum + self.height
        for (index,line,) in enumerate(self.formattedResults[top:bottom]):
            linenum = self.topLineNum + index
            lineString = self.format_line(line)

            if index != self.highlightLineNum:
                if line['category'] == 'title_bar':
                    self.win.addstr(index, 0, lineString, curses.A_BOLD)
                else:
                    self.win.addstr(index, 0, lineString)
            else:
                self.win.addstr(index, 0, lineString, curses.A_REVERSE)
        self.win.refresh()

    def updown(self, increment):
        nextLineNum = self.highlightLineNum + increment

        #Paging
        if increment == -1 and self.highlightLineNum == 0 and self.topLineNum != 0:
            self.topLineNum -= 1
            return
        elif increment == 1 and nextLineNum == self.height and (self.topLineNum + self.height) != len(self.formattedResults):
            self.topLineNum += 1
            return

        #Scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum + self.highlightLineNum + 1) != len(self.formattedResults) and self.highlightLineNum != len(self.formattedResults):
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

