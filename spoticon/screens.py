import curses
import io
import math
import pdb
import numpy
import time
import urllib.request as urllib

from PIL import Image


class Search_Screen(object):

    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        """ A curses sub-screen for displaying the results of a query

            Args:
                stdscreen (obj) = The main curses object for the program
                lines (int) = The line height for this screen
                columns (int) = The char width for this screen
                begin_y (int) = The number of lines from main screen top to begin screen
                begin_x (int) = The number of chars from main screen left to begin screen
        """

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
        """ Redraw window """

        self.win.refresh()

    def format_line(self, line):
        """ Return string representation of an object from formattedResults

            Args:
                line (obj) = The formattedResults object to be stringified
        """

        if line['category'] == 'track':
            return self.format_track(line)
        elif line['category'] == 'album_art':
            return self.format_album_art(line)
        elif line['category'] == 'album':
            return self.format_album()
        elif line['category'] == 'artist':
            return self.format_artist(line)
        elif line['category'] == 'playlist':
            return self.format_playlist(line)
        elif line['category'] == 'title_bar':
            return self.format_title_bar(line)
        else:
            return ''

    def format_track(self, track):
        """ Return string represenetation of a track object

            Args:
                track (obj) = The track object to be stringified
        """

        return '{0:<5} {1:<44} {2:^24} {3:>24}'.format(track.get('track_number'), track.get('track_name')[:30], track.get('album_name')[:20], track.get('artist_name')[:20])

    def format_album_art(self, line):
        """ Return string representation of the active album art line represented by the line object
            
            Args:
                line (obj) = The formattedResults representation of an album art line
        """

        if 'albums' in self.results and len(self.results['albums']) > 0:
            album = self.results['albums'][self.albumNumber]
            if not 'album_art' in album:
                album['album_art'] = self.asciinator(album['album_art_uri']['url'], 100)
            return '{0:<100}'.format(album['album_art'][line['line']][:100]) if len(album['album_art']) > line['line'] else '{0:<100}'.format('')
        else:
            return None

    def format_playlist(self, playlist):
        """ Return string representation of the playlist object

            Args:
                playlist (obj) = The playlist object to be stringified
        """

        return '{0:<100}'.format(playlist.get('playlist_name'))

    def format_album(self):
        """ Return string representation of the active album """

        return '{0:<100}'.format(self.results['albums'][self.albumNumber]['album_name'][:100])

    def format_artist(self, artist):
        """ Return string represntation of artist object

            Args:
                artist (obj) = The artist object to be stringified
        """

        return '{0:<100}'.format(artist.get('artist_name')[:50])

    def format_title_bar(self, title_bar):
        """ Return string representation of title_bar object

            Args:
                title_bar (obj) = The title object to be stringified
        """

        return '{0:<100}'.format(title_bar.get('title'))

    def get_highlighted_line(self):
        """ Return the object represented by the highlighted line """

        return self.formattedResults[self.highlightLineNum]

    def get_album(self):
        """ Return the active album that will be displayed """

        return self.results['albums'][self.albumNumber] if 'albums' in self.results and len(self.results['albums']) > 0 else None

    def format_results(self):
        """ Order search results into array """

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
        """ Draw the results on screen 

            Args:
                results(obj) = Formatted results of Spotify API query
        """

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
        """ Move highlighted line up and down

            Args:
                increment (int) = The number of lines to move the highlight bar
        """

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
        """ Move highlighted line left and right. Used for album art """

        if self.formattedResults and self.formattedResults[self.highlightLineNum]['category'] in ['album', 'album_art']:
            nextAlbumNumber = self.albumNumber + increment
            if nextAlbumNumber in range(len(self.results['albums'])):
                self.albumNumber = nextAlbumNumber


    # http://www.richard-h-clark.com/projects/block-art.html
    def asciinator(self, url, width):
        """ Return unicode representation of an image 

            Args:
                url (str) = A valid url for an image
                width (int) = The char width for the unicode image
        """

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
        """ A curses sub-screen for displaying the track currently playing

            Args:
                stdscreen (obj) = The main curses object for the program
                lines (int) = The line height for this screen
                columns (int) = The char width for this screen
                begin_y (int) = The number of lines from main screen top to begin screen
                begin_x (int) = The number of chars from main screen left to begin screen
        """
        
        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)
        self.win.border(1)

    def format_now_playing(self, track):
        """ Format display text for track for now playing screen """
        return ' {0}   -   {1}'.format(track.get('track_name'), track.get('artist_name'))

    def draw_screen(self, track):
        """ Draw the results on screen 

        Args:
            track (obj) = Track object to be displayed
        """ 
        self.win.clear()
        self.win.addstr(1, 5, self.format_now_playing(track))
        self.win.border(1)
        self.win.refresh()

class Input_Screen(object):
    
    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        """ A curses sub-screen for allowing and capturing user input

            Args:
                stdscreen (obj) = The main curses object for the program
                lines (int) = The line height for this screen
                columns (int) = The char width for this screen
                begin_y (int) = The number of lines from main screen top to begin screen
                begin_x (int) = The number of chars from main screen left to begin screen
        """

        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)
        self.win.clear()
        self.win.border(1)

    def get_user_input(self, displayMsg):
        """ Draw screen with displayMsg and return inputted text on enter key-press

            Args:
                displayMsg (str) = The message to display
        """

        self.win.addstr(1, 5, displayMsg)
        curses.curs_set(1)
        curses.echo()
        usrInput = self.win.getstr().decode(encoding='utf-8')
        curses.noecho()
        curses.curs_set(0)
        self.win.clear()
        del self.win

        return usrInput

class Message_Screen(object):
    
    def __init__(self, stdscreen, lines, columns, begin_y, begin_x):
        """ A curses sub-screen for displaying messages

        Args:
            stdscreen (obj) = The main curses object for the program
            lines (int) = The line height for this screen
            columns (int) = The char width for this screen
            begin_y (int) = The number of lines from main screen top to begin screen
            begin_x (int) = The number of chars from main screen left to begin screen
        """

        self.stdscreen = stdscreen
        self.height = lines
        self.width = columns

        self.win = self.stdscreen.derwin(self.height, self.width, begin_y, begin_x)
        self.win.clear()
        self.win.border(1)

    def flash_message(self, displayMsg, dur):
        """ Flash message in message screen

            Args:
                displayMsg (str) = The message to display
                dur (float) = The duration of the message
        """
        startStr = (int(self.width / 2) - int(len(displayMsg) / 2)) if len(displayMsg) < self.width else 0
        self.win.addstr(1, startStr, displayMsg[:self.width])
        self.win.refresh()
        time.sleep(dur)

