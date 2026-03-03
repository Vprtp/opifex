import random
import screenshot
import time
from pathlib import Path
import config
from config import Theme
from basemodule import BaseModule, ModuleResultType
from lib.ffmpeghandler import *

accountName:str = config.accountName

subtitlesTheme:Theme = config.subtitlesTheme

backgroundVideoSourcePool:list[str] = config.videoPool
dingSound:str = config.dingSound
htmlTemplate:str = config.titleHtmlTemplate

def Print(message:str,verbose:bool=True,last:str="\n"):
    if verbose:
        print(message,end=last)

def getBackgroundVideo(audioPath:str,sourcePool:list[str]) -> str:
    audioLenght:float = FFmpeg.getLength(audioPath)
    videoPath:str = sourcePool[random.randint(0,len(sourcePool)-1)]

    #concatenate videos until video is longer than audio
    while FFmpeg.getLength(videoPath) <= audioLenght:
        videoPathOld = videoPath
        videoPathNew = sourcePool[random.randint(0,len(sourcePool)-1)]
        if videoPathNew != videoPathOld:
            videoPath = f"{tempFolder}bg_{random.randint(10000,99999)}.mp4"
            FFmpeg.concatenate([videoPathOld,videoPathNew],videoPath)

    videoLenght:float = FFmpeg.getLength(videoPath)
    begin:float = random.uniform(0,videoLenght-audioLenght)

    #cut video lenght to be close to audio, for faster processing
    endPath:str = f"{tempFolder}bg_{random.randint(10000,99999)}.mp4"
    FFmpeg.cut(videoPath,begin,begin+audioLenght,endPath,reencode=False,roundUpOrDown=(False,True))
    return endPath

def computeVideo(endPath:str, title:str, subtitlesPath:str, titleAudioPath:str, textAudioPath:str, name:str=accountName, videoPool:list[str]=backgroundVideoSourcePool, ding:str=dingSound, sTheme:Theme=subtitlesTheme, html:str=htmlTemplate, verbose:bool=True) -> None:
    """
    Any file format for audio and video is allowed, as long as the format and the sampling rate are the same between each other. 
    For example, it's fine to have titleAudioPath's and textAudioPath's extensions as '.wav' and sampling rate 40kHz, as well as '.mp3' with rate 25kHz, 
    but the program breaks if, for example, the first is '.wav' and the second is '.mp3', or if they're both '.wav' but one's sampling rate is 20kHz and the other's 50kHz.
    Also, audio files should also have the same number of audio channels (all mono or all stereo, no in between)
    The same is valid for videoPool too: all contained videos must have the same extension.
    This is because, to save time, a lot of operations are done without any re-encoding.
    Converting files is simple, using FFmpeg:
    'ffmpeg -i input.mp3 -ar 22050 -ac 1 output.wav' will, for example, convert input.mp3 to output.wav with a sample rate of 20050 Hz and set its number of audio channels to 1 (mono)
    """
    startTime:float = time.time()
    Print("CREATING VIDEO", verbose=verbose)
    Print("Generating splash image...", verbose=verbose, last=" ")
    image:str = screenshot.process_html_to_image(html,data={"username":name,"content":title})
    tempFiles.append(image)
    titleLenght:float = FFmpeg.getLength(titleAudioPath)
    dingLenght:float = FFmpeg.getLength(ding)
    textLenght:float = FFmpeg.getLength(textAudioPath)
    finalAudio:str = f"{tempFolder}audio.wav"
    tempUncut:str = f"{tempFolder}uncut_{random.randint(10000,99999)}.mp4"
    tempCut:str = f"{tempFolder}cut_{random.randint(10000,99999)}.mp4"
    tempSubtitles:str = f"{tempFolder}srt_{random.randint(10000,99999)}.mp4"
    Print("Concatenating audio...", verbose=verbose)
    FFmpeg.concatenate([titleAudioPath,ding,textAudioPath],finalAudio)
    Print("Overlaying splash image, this might take a while...", verbose=verbose, last=" ")
    FFmpeg.overlayImage(getBackgroundVideo(finalAudio,videoPool),image,tempUncut, duration=(0,titleLenght+dingLenght), scale=1.0, center=True)
    Print("Cutting video...", verbose=verbose)
    FFmpeg.cut(tempUncut,0,titleLenght+dingLenght+textLenght,tempCut,reencode=False,roundUpOrDown=(False,True))
    Print("Adding subtitles, this might take a while, be patient...", verbose=verbose)
    FFmpeg.addSubtitles(tempCut,subtitlesPath,sTheme,tempSubtitles,offset=titleLenght+dingLenght)
    Print("Merging audio and video...", verbose=verbose, last=" ")
    FFmpeg.addAudioToVideo(finalAudio,tempSubtitles,endPath,isTemp=False)
    Print("Clearing temporary files...", verbose=verbose)
    FFmpeg.clearTemp()
    Print(f"Saved to {endPath}. Done in {round(time.time()-startTime,2)} seconds!", verbose=verbose)

class VideoGenerator(BaseModule):
    def __init__(self):
        self.name = "VideoGenerator"
        self.description = "Module for generating a short-form video based on given title, subtitles, audio for both title and text, and a destination path.\n\nParameters:\n-title: Title text\n-subtitles: Path to subtitles file\n-titleAudio: Path to the title audio file\n-textAudio: Path to the text audio file\n-destination: Destination path for the generated video"
        self.requiredArgs = [("title",str),("subtitles",str),("titleAudio",str),("textAudio",str),("destination",Path)]
        self.returnedDataTypes = []
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            computeVideo(str(kwargs["destination"].absolute()),kwargs["title"],kwargs["subtitles"],kwargs["titleAudio"],kwargs["textAudio"])
            return ModuleResultType(None,{})
        except Exception as e:
            return ModuleResultType(e,{})

