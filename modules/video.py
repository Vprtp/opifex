import os
import subprocess
import random
import screenshot
from fontTools.ttLib import TTFont
import datetime
import time
import re
import config
from config import Theme
from basemodule import BaseModule, ModuleResultType

# WARNING: THIS PROGRAM CURRENTLY ONLY WORKS ON LINUX

accountName:str = config.accountName

subtitlesTheme:Theme = config.subtitlesTheme

backgroundVideoSourcePool:list[str] = config.videoPool
dingSound:str = config.dingSound
htmlTemplate:str = config.titleHtmlTemplate

#vars used for ffmpeg processing
tempFiles:list[str] = []
tempFolder:str = config.tempFolder

def Print(message:str,verbose:bool=True,last:str="\n"):
    if verbose:
        print(message,end=last)

class FFmpeg:
    @staticmethod
    def getLength(path:str) -> float:
        result = subprocess.run(
            ["ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            path],
            capture_output=True,
            text=True
        )
        return float(result.stdout.strip())
    
    @staticmethod
    def getSize(path:str) -> tuple[int,int]: #returns (width,height), works for both pictures and videos
        result = subprocess.run([
            "ffprobe", 
            "-v", "error",
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height", 
            "-of", "csv=p=0", 
            path
        ], capture_output=True, text=True)
        result = result.stdout.strip().split(",")
        return (int(result[0]),int(result[1]))

    @staticmethod
    def getKeyframes(path:str) -> list[float]:
        # Run ffprobe to print keyframe timestamps as plain text
        cmd = [
            "ffprobe",
            "-select_streams", "v:0",
            "-v", "error",              # suppress info logs
            "-skip_frame", "nokey",
            "-show_frames",
            "-show_entries", "frame=best_effort_timestamp_time",
            "-of", "csv=p=0",
            path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Filter output lines to keep only numeric timestamps
        timestamps = []
        for line in result.stdout.splitlines():
            match = re.match(r'^(\d+(?:\.\d+)?)', line)
            if match:
                timestamps.append(float(match.group(1)))
        
        return timestamps

    @staticmethod
    def getClosestKeyframe(keyframes:list[float], time:float, direction:str="down") -> float: #direction="down" will round down, direction="up" will round up
        """
        Gets the closest keyframe to the given time.
        
        Args:
            keyframes (list): List of keyframe timestamps in seconds.
            time (float): Time in seconds to find closest keyframe.
            direction (str): "down" for rounding down, "up" for rounding up.
        
        Returns:
            float: Closest keyframe timestamp.
        """
        if direction == "down":
            return max([kf for kf in keyframes if kf <= time], default=keyframes[0])
        elif direction == "up":
            return min([kf for kf in keyframes if kf >= time], default=keyframes[-1])
        else:
            raise ValueError("Direction must be 'down' or 'up'")

    @staticmethod
    def clearTemp(files:list[str]=tempFiles) -> None:
        for file in files:
            try:
                os.remove(file)
            except:
                print(f"WARNING: unable to delete temporary file {file}")

    @staticmethod
    def getFontNameFromFile(font_path):
        font = TTFont(font_path)
        for record in font["name"].names:
            if record.nameID == 1:  # Font Family name
                return record.toUnicode()
        return None

    @staticmethod
    def shiftTimestamp(ts, offset) -> str:
        """Shift SRT timestamp string by offset (seconds)."""
        h, m, s = ts.split(":")
        s, ms = s.split(".")
        total = (int(h) * 3600 + int(m) * 60 + int(s) + int(ms)/1000) + offset
        if total < 0:
            total = 0
        # Convert back to H:MM:SS.MS format
        td = datetime.timedelta(seconds=total)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        cs = int(td.microseconds / 10000)
        return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{cs:03d}"

    @staticmethod
    def srtToAss(resolution:tuple[int,int],srt_file,ass_file,font_path,font_size=48,text_color="&H00FFFFFF",outline_color="&H00000000",outline_width=2,alignment=5,time_offset=0.0):
        """
        Converts SRT to ASS with custom font file, styles, and optional time offset.
        time_offset in seconds (can be negative or positive).
        """
        font_name = FFmpeg.getFontNameFromFile(font_path)
        if not font_name:
            raise ValueError("Could not read font name from file")

        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(f"""[Script Info]
    ScriptType: v4.00+
    PlayResX: {resolution[0]}
    PlayResY: {resolution[1]}
    Timer: 100.0000

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    Style: Default,{font_name},{font_size},{text_color},&H000000FF,{outline_color},&H64000000,0,0,0,0,100,100,0,0,1,{outline_width},1,{alignment},10,10,10,1

    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    """)

            with open(srt_file, "r", encoding="utf-8") as srt:
                lines = srt.read().splitlines()
                i = 0
                while i < len(lines):
                    if lines[i].strip().isdigit():
                        i += 1
                        if i >= len(lines): break
                        times = lines[i].replace(",", ".").split(" --> ")
                        start = FFmpeg.shiftTimestamp(times[0], time_offset)
                        end = FFmpeg.shiftTimestamp(times[1], time_offset)
                        i += 1
                        text_lines = []
                        while i < len(lines) and lines[i].strip() != "":
                            text_lines.append(lines[i])
                            i += 1
                        text = "\\N".join(text_lines).replace("{", "\\{")
                        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\pos({int(resolution[0]/2)},{int(resolution[1]/2)})}}{text}\n")
                    i += 1

    @staticmethod
    def concatenate(paths:list[str], endPath:str, isTemp=True) -> None: #if isTemp=True, endPath will be added to tempFiles, so it will be deleted when calling clearTemp
        textFile = tempFolder + os.path.splitext(os.path.basename(endPath))[0] + ".txt" #obtain the file path for the temporary text file to store the video paths, by concatenating tempFolder, the endPath file name (with no extension) and the extension ".txt"
        tempFiles.append(textFile)
        with open(textFile, "w") as f:
            for item in paths:
                f.write(f"file '{item}'\n")
        subprocess.run([
            "ffmpeg", 
            "-v", "error",
            "-safe", "0",
            "-f", "concat", 
            "-i", textFile, 
            "-c", "copy",
            endPath
        ])
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def cut(ogPath:str, begin:float, end:float, endPath:str, reencode:bool=True, roundUpOrDown:tuple[bool]=(True,True), isTemp=True) -> None: #if reencode=True, the video will be reencoded so the cut will be frame-perfect. else, the video will get rounded to the nearest keyframe. set roundUpOrDown to True to add excess frames, set it to False to cut them: since it's a tuple, this applies to both begin and end time
        if reencode:
            subprocess.run([
                "ffmpeg",
                "-v", "error",
                "-ss", str(begin), 
                "-to", str(end),
                "-i", ogPath,
                "-c:v", "libx264", 
                "-c:a", "aac",
                endPath
            ])
        else:
            keyframes:list[float] = FFmpeg.getKeyframes(ogPath)
            if roundUpOrDown[0]:
                beginClosestKeyframe:float = FFmpeg.getClosestKeyframe(keyframes, begin, direction="up")
            else:
                beginClosestKeyframe:float = FFmpeg.getClosestKeyframe(keyframes, begin, direction="down")
            if roundUpOrDown[1]:
                endClosestKeyframe:float = FFmpeg.getClosestKeyframe(keyframes, end, direction="up")
            else:
                endClosestKeyframe:float = FFmpeg.getClosestKeyframe(keyframes, end, direction="down")
            subprocess.run([
                "ffmpeg",
                "-v", "error",
                "-ss", str(beginClosestKeyframe), 
                "-to", str(endClosestKeyframe),
                "-i", ogPath,
                "-c", "copy",
                endPath
            ])
        
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def addAudioToVideo(audioPath:str, videoPath:str, endPath:str, isTemp=True) -> None: #will cut the longest of video or audio to fit the lenght of the shortes of the two
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", videoPath, 
            "-i", audioPath, 
            "-c:v", "copy", 
            "-map", "0:v:0", 
            "-map", "1:a:0",
            "-shortest", 
            endPath
        ])
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def overlayImage(videoPath:str, imagePath:str, endPath:str, duration:tuple[float]=(0,0.1), position:tuple[int,int]=(0,0), scale:float=1, center=False, isTemp=True): #duration=(begin time, end time) | position=(x,y) | scale changes the image size keeping it in proportion | if center=True the image will be centered in the video | isTemp=True will add the path to tempFiles, deleting it when clearTemp is called
        #cut video into parts to apply the overlay only on the interested one, makes processing quicker
        videoDuration:float = FFmpeg.getLength(videoPath)
        matchesVideo:bool = False
        concatList:list[str] = []
        ovPath:str = f"{tempFolder}ovr_{random.randint(10000,99999)}.mp4"
        if duration[0] == 0 and duration[1] == videoDuration:
            matchesVideo = True
            vPath:str = videoPath
            ovPath = endPath
        elif duration[0] == 0:
            after = f"{tempFolder}ovr-after_{random.randint(10000,99999)}.mp4"
            vPath = f"{tempFolder}ovr-during_{random.randint(10000,99999)}.mp4"
            FFmpeg.cut(videoPath,0,duration[1],vPath,reencode=False,roundUpOrDown=(False,True))
            FFmpeg.cut(videoPath,duration[1],videoDuration,after,reencode=False,roundUpOrDown=(True,True))
            concatList = [ovPath,after]
        elif duration[1] == videoDuration:
            before = f"{tempFolder}ovr-before_{random.randint(10000,99999)}.mp4"
            vPath = f"{tempFolder}ovr-during_{random.randint(10000,99999)}.mp4"
            FFmpeg.cut(videoPath,0,duration[0],before,reencode=False,roundUpOrDown=(False,False))
            FFmpeg.cut(videoPath,duration[0],videoDuration,vPath,reencode=False,roundUpOrDown=(False,True))
            concatList = [before,ovPath]
        else:
            before = f"{tempFolder}ovr-before_{random.randint(10000,99999)}.mp4"
            vPath = f"{tempFolder}ovr-during_{random.randint(10000,99999)}.mp4"
            after = f"{tempFolder}ovr-after_{random.randint(10000,99999)}.mp4"
            FFmpeg.cut(videoPath,0,duration[0],before,reencode=False,roundUpOrDown=(False,False))
            FFmpeg.cut(videoPath,duration[0],duration[1],vPath,reencode=False,roundUpOrDown=(False,True))
            FFmpeg.cut(videoPath,duration[1],videoDuration,after,reencode=False,roundUpOrDown=(True,True))
            concatList = [before,ovPath,after]
        
        imageSize:tuple[int,int] = FFmpeg.getSize(imagePath)
        overlayX:int = int(imageSize[0]*scale)
        overlayY:int = int(imageSize[1]*scale)
        posX:int = position[0]
        posY:int = position[1]
        if center:
            videoSize:tuple[int,int] = FFmpeg.getSize(vPath)
            posX = int((videoSize[0]-overlayX)/2)
            posY = int((videoSize[1]-overlayY)/2)
        # Build the filter string dynamically
        filter_complex = f"[1:v] scale={overlayX}:{overlayY} [ovrl];[0:v][ovrl] overlay={posX}:{posY}:enable='between(t,{duration[0]},{duration[1]})'"
        # Assemble the FFmpeg command
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", vPath,
            "-i", imagePath,
            "-filter_complex", filter_complex,
            "-c:a", "copy",
            ovPath
        ])

        tempFiles.append(ovPath)

        if not matchesVideo:
            FFmpeg.concatenate(concatList,endPath,isTemp)

        if isTemp and (not endPath in tempFiles):
            tempFiles.append(endPath)

    @staticmethod
    def addSubtitles(videoPath:str, subtitlesPath:str, theme:Theme, endPath:str, offset:float=0, isTemp=True):
        assFile = tempFolder + os.path.splitext(os.path.basename(subtitlesPath))[0] + ".ass" #obtain the file path for the ass subtitles file by concatenating tempFolder, the subtitlesPath file name (with no extension) and the extension ".ass"
        FFmpeg.srtToAss(FFmpeg.getSize(videoPath),subtitlesPath,assFile,theme.font,theme.fontSize,theme.color,theme.contourColor,theme.contourWidth,theme.alignment,offset)
        tempFiles.append(assFile)
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", videoPath, 
            "-vf", f"subtitles='{assFile}':fontsdir='{os.path.dirname(theme.font)}'",
            "-c:a", "copy",
            endPath
        ])
        if isTemp:
            tempFiles.append(endPath)


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
        self.description = "Module for generating a video based on given title, subtitles, audio for both title and text, and a destination path.\n\nParameters:\n-title: Title text\n-subtitles: Path to subtitles file\n-titleAudio: Path to the title audio file\n-textAudio: Path to the text audio file\n-destination: Destination path for the generated video"
        self.requiredArgs = [("title",str),("subtitles",str),("titleAudio",str),("textAudio",str),("destination",str)]
        self.returnedDataTypes = []
        self.dependencies = []
    
    def execute(self, **kwargs):
        try:
            computeVideo(kwargs["destination"],kwargs["title"],kwargs["subtitles"],kwargs["titleAudio"],kwargs["textAudio"])
            return ModuleResultType(None,{})
        except Exception as e:
            return ModuleResultType(e,{})