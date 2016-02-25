import curses
import io
import math
import pdb
import numpy
import urllib.request as urllib

from PIL import Image


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
        self.albumArtBegin = -1
        self.albumArtEnd = -1
        self.albumNumber = 0

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)

    def refresh(self):
        self.win.refresh()

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
        if albums in self.results and len(self.results['albums']) > 0:
            album = self.results['albums'][self.albumNumber]
            if not 'album_art' in album:
                album['album_art'] = self.asciinator(album['album_art_uri']['url'], 29/album['album_art_uri']['width'], 8)
            return '{0:<103}'.format(album['album_art'][line['line']][:100]) if len(album['album_art']) > line['line'] else '{0:<103}'.format('')
        else:
            return None

    def format_album(self, line):
        return '{0:<103}'.format(self.results['albums'][self.albumNumber]['album_name'][:100])

    def format_artist(self, artist):
        return '{0:<103}'.format(artist.get('artist_name')[:50])

    def format_title_bar(self, title_bar):
        return '{0:<103}'.format(title_bar.get('title'))

    def get_highlighted_line(self):
        return self.formattedResults[self.highlightLineNum]

    def get_album(self):
        return self.results['albums'][self.albumNumber] if albums in self.results and len(self.results['albums'] > 0) else None

    def format_results(self):
        self.formattedResults = []

        if 'artists' in self.results and len(self.results['artists']) > 0:
            self.formattedResults.append({
                'title': 'ARTISTS',
                'category': 'title_bar',
            })
            self.formattedResults += self.results['artists']

        if 'albums' in self.results and len(self.results['albums']) > 0:
            self.formattedResults.append({
                'title': 'ALBUMS',
                'category': 'title_bar',
            })
            self.albumArtBegin = len(self.formattedResults) + 1
            for x in range(25):
                self.formattedResults.append({ 'line': x, 'category': 'album_art' })
            self.albumArtEnd = len(self.formattedResults) 
            self.formattedResults.append({ 'category': 'album' })
        else:
            self.albumArtBegin = -1
            self.albumArtEnd = -1

        if 'tracks' in self.results and len(self.results['tracks']) > 0:
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
            self.albumNumber = 0
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

    def leftright(self, increment):
        if self.formattedResults and self.formattedResults[self.highlightLineNum]['category'] in ['album', 'album_art']:
            nextAlbumNumber = self.albumNumber + increment
            if nextAlbumNumber in range(len(self.results['albums'])):
                self.albumNumber = nextAlbumNumber


    # https://gist.github.com/cdiener/10491632
    def asciinator(self, url, scaling, intensity):
#       chars = numpy.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
        chars = numpy.asarray(list(u' ▗▖▄▝▐▞▟▘▚▌▙▀▜▛█'))
        widthCorrection = 4.5

        # Grab image url and open in PIL
        f = io.BytesIO(urllib.urlopen(url).read())
        img = Image.open(f)

        # Crop image for better ascii conversion
        width, height = img.size
        left = round(width/8)
        top = round(height/8)
        right = round(7 * width/8)
        bottom = round(7 * height/8)
        newimg = img.crop( ( left, top, right, bottom ) )

        # ASCII conversion magic
        newsize = (round(newimg.size[0]*scaling*widthCorrection), round(newimg.size[1]*scaling))
        newimg = numpy.sum(numpy.asarray(newimg.resize(newsize)), axis=2)
        newimg -= newimg.min()
        newimg = (1.0 - newimg/newimg.max())**intensity*(chars.size-1)
        return [a for a in ( ("".join(r) for r in chars[newimg.astype(int)] ) )]


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

