import video
import alignSRT
import tts
import time
import pathlib
import config
from basemodule import BaseModule, ModuleResultType
import traceback

def generate(titlesAndTexts:dict[str,str], accountName:str, verboseName:bool=True):
    if verboseName:
        print("SIMPLE VIDEO GENERATOR")
    initTime = time.time()
    paths:list[str] = []
    for title, desc in titlesAndTexts.items():
        loc:tuple[str,str] = tts.generate(title,desc)
        print(f"Saved files in {loc[0]} and {loc[1]}")
        parentDir:str = str(pathlib.Path(loc[1]).parents[0])
        sub:str = alignSRT.generateSubtitles(loc[1],tts.cleanText(desc),parentDir)[1]
        print(f"Saved subtitles in {sub}")
        outputFile:str = config.videoOutputFolder+pathlib.Path(parentDir).name+".mp4"
        video.computeVideo(outputFile,title,sub,loc[0],loc[1],name=accountName)
        paths.append(outputFile)
    print(f"\n\nTask completed successfully in {time.time()-initTime} seconds.\nAverage time per video: {(time.time()-initTime)/len(titlesAndTexts)}")
    return paths

class SimpleVideoGenerator(BaseModule):
    def __init__(self):
        self.name = "SimpleVideoGenerator"
        self.description = "Module that generates videos based on a given title and text. Returns paths to the generated videos (list of size 1 when only one video is generated)\n\nParameters:\n-content: Dictionary of titles and texts for each generated video\n-accountName: credits that will be shown in the video"
        self.requiredArgs = [("content",dict[str,str]),("accountName",str)]
        self.returnedDataTypes = [("paths",list[str])]
        self.dependencies = ["TTS","Aligner","VideoGenerator"]
    
    def execute(self, version:str, **kwargs):
        try:
            paths:list[str]= generate(kwargs["content"],kwargs["accountName"])
            return ModuleResultType(None,{"paths":paths})
        except Exception as e:
            print(traceback.format_exc())
            return ModuleResultType(e,{})
