from fastapi import FastAPI

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
def main():
    pass

if __name__=="__main__":
    main()