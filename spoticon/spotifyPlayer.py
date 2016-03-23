import subprocess

class Spotify_Player(object):

    def make_apple_script(self, cmd):
        return ['osascript', '-e', cmd]
 
    def send_script(self, cmd, response=False):
        script = self.make_apple_script(cmd)
        if response:
            res = subprocess.check_output(script)
            return self.bytes_to_string(res)
        else:
            subprocess.call(script)

    def bytes_to_string(self, byts):
        return byts.decode('utf-8').rstrip()

    def play_track(self, track):
        try:
            self.send_script('tell application "Spotify" to play track "{0}"'.format(track['track_uri']))
        except:
            pass

    def play_pause(self):
        try:
            self.send_script('tell application "Spotify" to playpause')
        except:
            pass

    def get_player_state(self):
        try:
            return self.send_script('tell application "Spotify" \n get player state \n end tell', True)
        except:
            pass

    def get_player_position(self):
        try:
            return self.send_script('tell application "Spotify" \n get player position \n end tell', True)
        except:
            pass

