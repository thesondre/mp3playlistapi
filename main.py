from fastapi import FastAPI
import os, eyed3, math
from time import strftime, gmtime
app = FastAPI()

config = {
    "mp3Dir":"~/Music",
    "playlistDir":"~/Music/Playlists",
    "relativePath":"../"
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
        "relativePath":"../"
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
                audioTitle = audioFile.tag.title if audioFile.tag.title is not None else "Unknown Title"
                albumName = audioFile.tag.album if audioFile.tag.album is not None else "Unknown Album"
                artistName = audioFile.tag.artist if audioFile.tag.artist is not None else "Unknown Artist"
                duration = math.floor(audioFile.info.time_secs)
                files.append({"Title":audioTitle, "Artist":artistName, "Album":albumName, "Path":audioFile.path, "Duration":strftime("%M:%S", gmtime(duration))})

    return list(files)
def main():
    print(os.scandir(os.path.expanduser(config["mp3Dir"])))

if __name__=="__main__":
    main()