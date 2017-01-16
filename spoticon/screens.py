import curses
import io
import math
import time

import urllib.request as urllib
from PIL import Image


class Window(object):

    def __init__(self, stdScreen, height, width, beginY, beginX):
        """ A curses window
            Args:
                stdScreen (obj) = The main curses object for the program
                lines (int) = The line height for this window
                columns (int) = The char width for this window
                beginY (int) = The number of lines from main screen top to begin window
                beginX (int) = The number of chars from main screen left to begin window
        """
        self.stdScreen = stdScreen
        self.height = height
        self.width = width
        self.beginY = beginY
        self.beginX = beginX
        self.win = None

        self.create_win()

    def create_win(self):
        """ Create the curses window """
        self.win = self.stdScreen.derwin(self.height, self.width, self.beginY, self.beginX)
        self.win.clear()
        self.win.border(1)


class Scroll_Window(Window):

    def __init__(self, *args, **kwargs):
        """ A scrolling curses window """
        Window.__init__(self, *args, **kwargs)

        self.lines = self.orderedLines = []
        self.topLineNum = 0
        self.highlightLineNum = 0

    def add_line(self, index, line, highlighted):
        """ Draw a line in curses window
            Args:
                index (int) = The window line to draw on
                line (obj) = The object to stringify and draw
                highlighted (bool) = Whether to highlight line
        """
        pass

    def order_lines(self):
        """ Order lines for correct display order """
        self.orderedLines = self.lines

    def get_highlighted_line(self):
        """ Return the object represented by the highlighted line """
        return self.orderedLines[self.highlightLineNum] if self.orderedLines else None

    def draw_screen(self, lines=None):
        """ Draw the results on screen 
            Args:
                lines (array) = Lines to draw in window
        """
        if lines and lines != self.lines:
            self.lines = lines
            self.order_lines()
            self.topLineNum = 0
            self.highlightLineNum = 0

        self.win.erase()
        top = self.topLineNum
        bottom = self.topLineNum + self.height

        for (index,line,) in enumerate(self.orderedLines[top:bottom]):
            linenum = self.topLineNum + index
            highlighted = (index == self.highlightLineNum)
            self.add_line(index, line, highlighted)

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
            self.draw_screen()
            return
        elif increment == 1 and nextLineNum == self.height and (self.topLineNum + self.height) != len(self.orderedLines):
            self.topLineNum += 1
            self.draw_screen()
            return

        #Scroll highlight line
        if increment == -1 and (self.topLineNum != 0 or self.highlightLineNum != 0):
            self.highlightLineNum = nextLineNum
        elif increment == 1 and (self.topLineNum + self.highlightLineNum + 1) != len(self.orderedLines) and self.highlightLineNum != len(self.orderedLines):
            self.highlightLineNum = nextLineNum
        
        self.draw_screen()

class Results_Window(Scroll_Window):

    def __init__(self, *args, **kwargs):
        """ The curses display window for results """
        Scroll_Window.__init__(self, *args, **kwargs)

        self.albumArtBegin = -1
        self.albumArtEnd = -1
        self.albumNumber = 0

    def draw_screen(self, lines=None):
        """ Draw the results on screen
            Args:
                lines (array) = Loines to draw in window
        """
        if lines and lines != self.lines:
            self.albumArtBegin = -1
            self.albumArtEnd = -1
            self.albumNumber = 0
        Scroll_Window.draw_screen(self, lines=lines)

    def add_line(self, index, line, highlighted):
        """ Draw a line in curses window
            Args:
                index (int) = The window line to draw on
                line (obj) = The object to stringify and draw
                highlighted (bool) = Whether to highlight line
        """
        stringifiedLine = self.stringify_line(line)
        if highlighted:
            self.win.addstr(index, 0, stringifiedLine, curses.A_REVERSE)
        elif line['category'] == 'title_bar':
            self.win.addstr(index, 0, stringifiedLine, curses.A_BOLD)
        else:
            self.win.addstr(index, 0, stringifiedLine)

    def leftright(self, increment):
        """ Move highlighted line left and right. Used for album art """
        if self.orderedLines and self.orderedLines[self.highlightLineNum]['category'] in ['album', 'album_art']:
            nextAlbumNumber = self.albumNumber + increment
            if nextAlbumNumber in range(len(self.lines['albums'])):
                self.albumNumber = nextAlbumNumber

        self.draw_screen()

    def stringify_line(self, line):
        """ Return string representation of line
            Args:
                line (obj) = The object to be stringified
        """
        if line['category'] == 'title_bar':
            return '{0:<100}'.format(line.get('title'))
        elif line['category'] == 'artist':
            return '{0:<100}'.format(line.get('artist_name')[:50])
        elif line['category'] == 'track':
            return '{0:<5} {1:<44} {2:^24} {3:>24}'.format(line.get('track_number'), line.get('track_name')[:30], line.get('album_name')[:20], line.get('artist_name')[:20])
        elif line['category'] == 'playlist':
            return '{0:<100}'.format(line.get('playlist_name'))
        elif line['category'] == 'album':
            return '{0:<100}'.format(self.lines['albums'][self.albumNumber]['album_name'][:100])
        elif line['category'] == 'album_art':
                album = self.lines['albums'][self.albumNumber]
                if not 'album_art' in album:
                    album['album_art'] = self.asciinator(album['album_art_uri']['url'], 100)
                return '{0:<100}'.format(album['album_art'][line['line']][:100]) if len(album['album_art']) > line['line'] else '{0:<100}'.format('')

    def get_album(self):
        """ Return the active album that will be displayed """
        return self.lines['albums'][self.albumNumber] if 'albums' in self.lines and len(self.lines['albums']) > 0 else None

    def order_lines(self):
        """ Order search results into array """
        self.orderedLines= []

        if 'playlists' in self.lines and len(self.lines['playlists']):
            self.orderedLines.append({
                'title': 'PLAYLISTS',
                'category': 'title_bar',
            })
            self.orderedLines += self.lines['playlists']

        if 'artists' in self.lines and len(self.lines['artists']):
            self.orderedLines.append({
                'title': 'ARTISTS',
                'category': 'title_bar',
            })
            self.orderedLines += self.lines['artists']

        if 'albums' in self.lines and len(self.lines['albums']):
            self.orderedLines.append({
                'title': 'ALBUMS',
                'category': 'title_bar',
            })
            self.albumArtBegin = len(self.orderedLines) + 1
            for x in range(35):
                self.orderedLines.append({ 'line': x, 'category': 'album_art' })
            self.albumArtEnd = len(self.orderedLines) 
            self.orderedLines.append({ 'category': 'album' })
        else:
            self.albumArtBegin = -1
            self.albumArtEnd = -1

        if 'tracks' in self.lines:
            self.orderedLines.append({
                'title': 'TRACKS',
                'category': 'title_bar',
            })
            self.orderedLines += self.lines['tracks']

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

        # Crop image
        img_width, img_height = orig_image.size
        orig_image = orig_image.crop((0, int(img_height*.2), img_width, int(img_height*.8)))

        # Resize the image so that the aspect ratio is correct 
        # for the characters. Ensure that the dimensions are 
        # multiples of two (two pixels per character).
        new_width = int(math.ceil(width / 2.0) * 2) * 2
        new_height = int(math.ceil(new_width / 6.0)) * 2
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


class Now_Playing_Window(Window):

    def __init__(self, *args, **kwargs):
        """ The curses display window for the current track """
        self.currentTrack = None
        Window.__init__(self, *args, **kwargs)

    def draw_screen(self, track=None, repeat=False):
        """ Draw the results in the curses window
        Args:
            track (obj) = Track object to be displayed
            repeat (bool) = Whether track repeat is on
        """ 
        if track:
            self.win.clear()
            self.win.addstr(1, 5, self.format_now_playing(track))
            self.win.border(1)
        self.win.refresh()

    def format_now_playing(self, track):
        """ Format display text for track for now playing screen """
        return ' {0}   -   {1}'.format(track.get('track_name'), track.get('artist_name'))

class Input_Window(Window):
    
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
        del self.win

        return usrInput

class Message_Window(Window):
    
    def flash_message(self, displayMsg, dur):
        """ Flash message in message screen
            Args:
                displayMsg (str) = The message to display
                dur (float) = The duration of the message
        """
        self.win.clear()
        startX = (int(self.width / 2) - int(len(displayMsg) / 2)) if len(displayMsg) < self.width else 0
        self.win.addstr(1, startX, displayMsg[:self.width])
        self.win.refresh()
        time.sleep(dur)
        del self.win

class Help_Window(Window):

    def __init__(self, *args, **kwargs):
        """ A curses window to dispaly help information """
        Window.__init__(self, *args, **kwargs)
        self.help_text = '''
      ▗▄▄▄▄▄
   ▗▄████████▙▖
   ▟███████████▄
  █████████████▛
 ▐████████████▛ ▗▄▄▄▄▄▄▄▖      ▗▄▄▄▄▄  ▗▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄     ▗▄▄▄▄▖    ▗▄▄▄▄▖   ▄▄▄▄▖   ▄▄▄▄
 ██████    ▝▀▛  ▐█████████▙▖  ▟██████▙▖▐████████████████████████   ▄███████▙▖▗▟██████▙▖ ████▙   ████
 ██████         ▐███████████▖▟█████████▟████████████████████████  ▟████████████████████▖█████▖  ████
 ███████▄▖      ▐███████████████████████████████████████████████ ▟██████████▜████████████████▌  ████
 ▐█████████▄    ▐███▌   ▝███████▛  ▝████▌   ████▌       ████▌   ▗████▛    ▀ ████▛  ▐██████████  ████
  ▜██████████▙▖ ▐███▌    ███████▘   ▜███▙   ████▌       ████▌   ▟████▘     ▐████▘   ██████████▖ ████
   ▜███████████▖▐███▌   ▗███████    ▐████   ████▌       ████▌   ████▌      ▐████    ▐██████▌██▙ ████
    ▝▜██████████▟███▌  ▗████████    ▐████   ████▌       ████▌   ████▌      ▐████    ▐██████▌▐██▖▜███
       ▀▜███████████████████████    ▐████   ████▌       ████▌   ████▌      ▐████    ▐███████▝██▌▐███
         ▝▜████████████████▜████    ▐████   ████▌       ████▌   ████▌      ▐████    ▐███████ ▜██▐███
   ▄▖      ██████████████▀▘▐████    ▐████   ████▌       ████▌   ████▙      ▐████    ▟███████ ▐██████
  ▟███▄▖  ▄█████████▌      ▝████▌   ████▌   ████▌       ████▌   ▐████▙    ▗▞████▌  ▗████████  ██████
 ███████████████▜███▌       ▜████▙▄▟████    ████▌   ▄▄▄▄████▙▄▄▄ █████▙▄▄▟███████▄▄▟████████  ▜█████
▐██████████████▀▐███▌       ▝██████████▛    ████▌   ████████████ ▝█████████████████████▛████  ▝█████
 ▝████████████▘ ▐███▌        ▝████████▛     ████▌   ████████████  ▝█████████▛▝████████▛ ████   ▜████
   ▝▀███████▀   ▐███▌          ▀█████▘      ████▌   ████████████    ▀█████▛▘   ▀████▛▘  ████   ▐████
                                                                                    by Stephen Price
                                         Press ? For Help

s:      Open Searchbox           a:      Get Track Album            +:      Add Track To Queue
ENTER:  Activate Line            A:      Get Track Artist           .:      Add All Tracks To Queue
j:      Move Down                SPACE:  Play/Pause Player          L:      Play Next Queued Song
k:      Move Up                  r:      Toggle Repeat One Track    H:      Play Previous Queued Song
l:      Move Right               p:      Open My Playlists          C:      Clear Queue
h:      Move Left                f:      Next in Search History     q:      Display Queue
                                 p:      Open My Playlists
'''
    def draw_screen(self):
        self.win.addstr(0, 0, self.help_text)
        self.win.refresh()

