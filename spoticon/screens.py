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
        elif line['category'] == 'playlist':
            return self.format_playlist(line)
        elif line['category'] == 'title_bar':
            return self.format_title_bar(line)
        else:
            return ''

    def format_track(self, track):
        return '{0:<5} {1:<44} {2:^24} {3:>24}'.format(track.get('track_number'), track.get('track_name')[:30], track.get('album_name')[:20], track.get('artist_name')[:20])

    def format_album_art(self, line):
        if 'albums' in self.results and len(self.results['albums']) > 0:
            album = self.results['albums'][self.albumNumber]
            if not 'album_art' in album:
                album['album_art'] = self.asciinator(album['album_art_uri']['url'], 100)
            return '{0:<100}'.format(album['album_art'][line['line']][:100]) if len(album['album_art']) > line['line'] else '{0:<100}'.format('')
        else:
            return None

    def format_playlist(self, line):
        return '{0:<100}'.format(line.get('playlist_name'))

    def format_album(self, line):
        return '{0:<100}'.format(self.results['albums'][self.albumNumber]['album_name'][:100])

    def format_artist(self, artist):
        return '{0:<100}'.format(artist.get('artist_name')[:50])

    def format_title_bar(self, title_bar):
        return '{0:<100}'.format(title_bar.get('title'))

    def get_highlighted_line(self):
        return self.formattedResults[self.highlightLineNum]

    def get_album(self):
        return self.results['albums'][self.albumNumber] if 'albums' in self.results and len(self.results['albums']) > 0 else None

    def format_results(self):
        self.formattedResults = []

        if 'playlists' in self.results:
            self.formattedResults.append({
                'title': 'PLAYLISTS',
                'category': 'title_bar',
            })
            self.formattedResults += self.results['playlists']

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
            self.albumArtBegin = len(self.formattedResults) + 1
            for x in range(25):
                self.formattedResults.append({ 'line': x, 'category': 'album_art' })
            self.albumArtEnd = len(self.formattedResults) 
            self.formattedResults.append({ 'category': 'album' })
        else:
            self.albumArtBegin = -1
            self.albumArtEnd = -1

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


    # http://www.richard-h-clark.com/projects/block-art.html
    def asciinator(self, url, width):
        CHAR_SEQ = u'█▛▜▀▙▌▚▘▟▞▐▝▄▖▗ '

        # Open the image and convert it to black and white
        FILE_NAME = io.BytesIO(urllib.urlopen(url).read())
        orig_image = Image.open(FILE_NAME)

        if orig_image.mode == 'RGBA':
            # Remove transparancy
            bg_image = Image.new("RGBA", 
                                     orig_image.size, 
                                     "white")
            bg_image.paste(orig_image, (0,0), orig_image)
            orig_image = bg_image

        if orig_image.mode != '1':
            # Convert the image to black and white
            # Converting to 'P' first results in better conversion
            orig_image = orig_image.convert('P').convert('1')

        # Resize the image so that the aspect ratio is correct 
        # for the characters. Ensure that the dimensions are 
        # multiples of two (two pixels per character).
        new_width = int(math.ceil(width / 2.0) * 2) * 2
        new_height = int(math.ceil(new_width / 4.0)) * 2
        image = orig_image.resize((new_width, new_height), Image.ANTIALIAS)

        # Get the pixel data
        pix = image.load()

        # The value above which pixels are considered white and 
        # below which pixels are considered black.
        THRESHOLD = 255

        lines = []

        # Itereate over all the pixels and generate the unicode 
        # representation. Print it to stdout.
        for y in range(0, new_height, 2):
            s = ''
            for x in range(0, new_width, 2):
                char_index = int(pix[x, y] / THRESHOLD * 8) + int(pix[x+1, y] / THRESHOLD * 4) + int(pix[x, y+1] / THRESHOLD * 2) + int(pix[x+1, y+1] / THRESHOLD)
                s += CHAR_SEQ[char_index]
            lines.append(s)

        return lines

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

