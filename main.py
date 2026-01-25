from fastapi import FastAPI
from pydantic import BaseModel
import xml.etree.ElementTree as ET
import os, eyed3
from time import strftime, gmtime
app = FastAPI()

config = {
    "mp3Dir":"~/Music",
    "playlistDir":"~/Music/Playlists",
    "relativePath":"../",
    "playlistFormat":"xspf"
}
@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

##Config
#############################################################################################
@app.get("/config")
def get_config():
    return config

@app.patch("/config")
def change_config(mp3Dir:str, playlistDir:str, relativePath:str):
    
    if(mp3Dir):
        config["mp3Dir"] = mp3Dir
    if(playlistDir):
        config["playlistDir"] = playlistDir
    if(relativePath):
        config["relativePath"] = relativePath
    return config

@app.post("/config/reset")          #Default setting
def reset_config():
   global config 
   config = { 
        "mp3Dir":"~/Music",
        "playlistDir":"~/Music/Playlists",
        "relativePath":"../",
        "playlistFormat":"xspf"
    }
   return "Config resetted"
#############################################################################################
#Mp3 files
@app.get("/mp3")
def get_mp3():
    files = []
    with os.scandir(os.path.expanduser(config["mp3Dir"])) as mp3s:
        for mp3 in mp3s:
            if mp3.name.endswith(".mp3"):
                audioFile = eyed3.load(f"{os.path.expanduser(config["mp3Dir"])}/{mp3.name}")        
                audioTitle =  audioFile.tag.title if audioFile.tag.title else mp3.name
                albumName = audioFile.tag.album if audioFile.tag.album else "Unknown"
                artistName = audioFile.tag.artist if audioFile.tag.artist else "Unknown"
                duration = audioFile.info.time_secs
                files.append({"Title":audioTitle, "Artist":artistName, "Album":albumName, "globalPath":audioFile.path, "relativePath":config["relativePath"]+mp3.name, "Duration":strftime("%M:%S", gmtime(duration))})
    return list(files)
#############################################################################################
###For reading the contents in playlist files.
def parseXSPF (xspf): 
    
    tree = ET.parse(xspf)

    root = tree.getroot()

    media = []

    ns = {'xspf': 'http://xspf.org/ns/0/'}
    for track in root.findall('xspf:trackList/xspf:track', ns):
        #title = track.find('xspf:title', ns ).text
        location = (track.find('xspf:location', ns ).text).replace("%20", " ") 
        media.append(dict({"path":location}))

    parsed = {
        "title":root.find('xspf:title', ns).text,
        "tracks":media
    }
    return  parsed

#############################################################################################
#Playlist

@app.get("/playlists")
def get_playlists():
    playlists = []
    with os.scandir(os.path.expanduser(config["playlistDir"])) as files:
        for file in files:
            if file.name.endswith(config["playlistFormat"]):
                playlists.append(parseXSPF(file.path))
    return playlists

@app.get("/playlists/{playlist}")
def get_playlist(playlist):
    with os.scandir(os.path.expanduser(config["playlistDir"])) as files:
        for file in files:
            if file.name.endswith(config["playlistFormat"]):
                parsed = parseXSPF(file.path)
                if parsed["title"] == playlist:
                    return parsed
    
    return "Playlist does not exist"
class Playlist(BaseModel):
    name:str
    tracks:list[str]

@app.post("/playlists")
def create_playlist(playlist:Playlist):
    tracklist = ""
    trackID = ""
    count = 0
    for track in playlist.tracks:
        tracklist += f"""<track>
			<location>{track}</location>
			<extension application="http://www.videolan.org/vlc/playlist/0">
				<vlc:id>{count}</vlc:id>
				<vlc:option>recursive=collapse</vlc:option>
			</extension>
		</track>""".replace("&","&amp;")
        trackID += f'<vlc:item tid="{count}"/>'
        count += 1
    with open(f"{os.path.expanduser(config["playlistDir"])}/{playlist.name}.xspf", "w") as file:
        file.write(f"""<?xml version="1.0" encoding="UTF-8"?>
    <playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
	    <title>{playlist.name}</title>
	    <trackList>
		    {tracklist}
        </trackList>
    	<extension application="http://www.videolan.org/vlc/playlist/0">
		{trackID}:
	    </extension>
    </playlist>
    """)
        return "Playlist created"