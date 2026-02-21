from fastapi import FastAPI, File, UploadFile
from fastapi.responses import *
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import xml.etree.ElementTree as ET
import os, eyed3, io, base64
from PIL import Image
from time import strftime, gmtime
from typing import List, Optional
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
config = {
    "mp3Dir":"~/Music",
    "playlistDir":"~/Music/Playlists",
    "relativePath":"../",
    "playlistFormat":"xspf"
}
@app.get("/", response_class=StreamingResponse
)
async def read_root():
    
    file = eyed3.load("/home/Sondre/Music/Bomb Iran (1980) - Vince Vance & The Valiants.mp3")
    imageData = file.tag.images
    if not imageData:
        pass
    image = Image.open(io.BytesIO(imageData[0].image_data))

    img_byte_arr = io.BytesIO()

    image.save(img_byte_arr, format="PNG")

    img_byte_arr.seek(0)
    return StreamingResponse(img_byte_arr, media_type="image/png")
    

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
class AudioMetadata(BaseModel):
    Title: str
    Artist: str
    Album: str
    globalPath:str
    relativePath:str
    Duration:str




@app.get("/mp3")
async def get_mp3():
    metadataList = []
    with os.scandir(os.path.expanduser(config["mp3Dir"])) as mp3s:
        for mp3 in mp3s:
            if mp3.name.endswith(".mp3"):
                audioFile = eyed3.load(f"{os.path.expanduser(config["mp3Dir"])}/{mp3.name}")
                if not audioFile.tag:
                    metadataList.append(AudioMetadata(Title=None, Image=None, Artist=None, Album=None, globalPath=audioFile.path, relativePath=config["relativePath"]+mp3.name, Duration=strftime("%M:%S", gmtime(audioFile.info.time_secs))))
                    continue
                    
                audioTitle =  audioFile.tag.title if audioFile.tag.title else mp3.name
                albumName = audioFile.tag.album if audioFile.tag.album else "Unknown"
                artistName = audioFile.tag.artist if audioFile.tag.artist else "Unknown"
                duration = strftime("%M:%S", gmtime(audioFile.info.time_secs))

                metadata = AudioMetadata(
                    Title=audioTitle,
                    Album=albumName,
                    Artist=artistName,
                    globalPath=audioFile.path,
                    relativePath=config["relativePath"]+mp3.name,
                    Duration=duration
                )
                metadataList.append(metadata)
    return metadataList
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
		{trackID}:Artist=artistName
	    </extension>
    </playlist>
    """)
        return "Playlist created"