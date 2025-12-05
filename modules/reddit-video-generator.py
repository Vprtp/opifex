import unshortenURL
import reddit
import video
import alignSRT
import tts
import time
import pathlib
import config
from basemodule import BaseModule, ModuleResultType
import traceback

def generate(url:str, commsOrDesc:bool, accountName:str):
    print("REDDIT VIDEO GENERATOR")
    initTime = time.time()
    url = unshortenURL.getUrl(url)
    a = reddit.getJSON(url)
    title:str = reddit.getTitle(a)
    paths:list[str] = []
    print(f"Title: '{title}' Upvotes: {reddit.getUpvotes(a)} Mode: {"comments" if commsOrDesc else "description"}")
    if commsOrDesc:
        comments:list[str] = reddit.getComments(a)
        for i in range(len(comments)):
            print(f"COMMENT {i}:\n{comments[i]}")
            loc:tuple[str,str] = tts.generate(reddit.getTitle(a),comments[i])
            print(f"Saved files in {loc[0]} and {loc[1]}")
            parentDir:str = str(pathlib.Path(loc[1]).parents[0])
            sub:str = alignSRT.generateSubtitles(loc[1],tts.cleanText(comments[i]),parentDir)[1]
            print(f"Saved subtitles in {sub}")
            outputFile:str = config.videoOutputFolder+pathlib.Path(parentDir).name+".mp4"
            video.computeVideo(outputFile,title,sub,loc[0],loc[1],name=accountName)
            paths.append(outputFile)
        print(f"\n\nTask completed successfully in {time.time()-initTime} seconds.\nAverage time per comment: {(time.time()-initTime)/len(comments)}")
    else:
        desc:str = reddit.getDescription(a)
        loc:tuple[str,str] = tts.generate(reddit.getTitle(a),desc)
        print(f"Saved files in {loc[0]} and {loc[1]}")
        parentDir:str = str(pathlib.Path(loc[1]).parents[0])
        sub:str = alignSRT.generateSubtitles(loc[1],tts.cleanText(desc),parentDir)[1]
        outputFile:str = config.videoOutputFolder+pathlib.Path(parentDir).name+".mp4"
        video.computeVideo(outputFile,title,sub,loc[0],loc[1],name=accountName)
        print(f"\n\nTask completed successfully in {time.time()-initTime} seconds.")
        paths = [outputFile]
    return paths

class RedditVideoGenerator(BaseModule):
    def __init__(self):
        self.name = "RedditVideoGenerator"
        self.description = "Module that generates a video, or multiple videos, based on the content contained in a given Reddit post. Returns paths to the generated videos (list of size 1 when only one video is generated)\n\nParameters:\n-url: URL to the Reddit post\n-commentsOrDesc: whether to generate multiple videos based on the comments (True) or to generate one video from the post's description (False)\n-accountName: credits that will be shown in the video"
        self.requiredArgs = [("url",str),("commentsOrDesc",bool),("accountName",str)]
        self.returnedDataTypes = [("paths",list[str])]
        self.dependencies = ["Reddit","TTS","Aligner","VideoGenerator","URLunshortener"]
    
    def execute(self, version:str, **kwargs):
        try:
            paths:list[str]= generate(kwargs["url"],kwargs["commentsOrDesc"],kwargs["accountName"])
            return ModuleResultType(None,{"paths":paths})
        except Exception as e:
            print(traceback.format_exc())
            return ModuleResultType(e,{})
