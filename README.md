# Spoticon

A mouseless Spotify UI in your terminal for Mac OSX using Python3. 

## Requirements

* Python 3
* A Spotify Premium account

## Installing / Getting started

Before getting started, log into your Spotify account, head over to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
and set up a new spotify application. Once created, you will need to add `http://localhost:8081` as 
a redirect uri. You will need the application client_id and client_secret later.

```
git clone https://github.com/stephenbprice/Spoticon.git
cd Spoticon
python setup.py install
touch ~/.spoticonrc
```

Open `~/.spoticonrc` and add the following lines:
```
username <your spotify username>
client_id <your spotify application client_id>
client_secret <your spotify application client_secret>
redirect_uri http://localhost:8081
```


Start the application by typing `spoticon` in your terminal
