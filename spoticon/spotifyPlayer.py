import subprocess

class Spotify_Player(object):

    def make_apple_script(self, cmd):
        """ Format apple script

            Args:
                cmd (str) = The applescript string
        """

        return ['osascript', '-e', cmd]
 
    def send_script(self, cmd, response=False):
        """ Send apple script and return formatted response

            Args:
                cmd (str) = The applescript string
                response (boolean) = Whether to expect and return a response from the applescript call
        """

        script = self.make_apple_script(cmd)
        if response:
            res = subprocess.check_output(script)
            return self.bytes_to_string(res)
        else:
            subprocess.call(script)

    def bytes_to_string(self, byts):
        """ Convert bytes to UTF-8 endoded string

            Args:
                bytes (bytes) = The bytes to convert
        """

        return byts.decode('utf-8').rstrip()

    def play_track(self, track_uri):
        """ Command Spotify player to play track

            Args:
                track_uri (str) = The Spotify API track uri for the track to be played
        """

        try:
            self.send_script('tell application "Spotify" to play track "{0}"'.format(track_uri))
        except:
            pass

    def play_pause(self):
        """ Command Spotify to toggle play/pause """    

        try:
            self.send_script('tell application "Spotify" to playpause')
        except:
            pass

    def get_player_state(self):
        """ Get and return Spotify Player state """

        try:
            return self.send_script('tell application "Spotify" \n get player state \n end tell', True)
        except:
            pass

    def get_player_position(self):
        """ Get and return Spotify Player position """

        try:
            return self.send_script('tell application "Spotify" \n get player position \n end tell', True)
        except:
            pass

