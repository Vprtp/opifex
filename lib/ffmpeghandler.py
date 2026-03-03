import os
import platform
import subprocess
import random
from fontTools.misc.arrayTools import offsetRect
from fontTools.ttLib import TTFont
import datetime
import re
from PIL import Image
from config import Theme, tempFolder

#vars used for ffmpeg processing
tempFiles:list[str] = []

class ImageProcessing:
    @staticmethod
    def resize(image_path, output_path, target_size, method='stretch'):
        """Resize image and save to file using PIL"""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if img.mode not in ('RGB', 'L'):  # L is grayscale
                img = img.convert('RGB')
            
            if method == 'stretch':
                # Stretch/scale to exact dimensions
                resized = img.resize(target_size, Image.Resampling.LANCZOS)
                resized.save(output_path)
                
            elif method == 'cut':
                # Center crop to target aspect ratio, then resize
                img_ratio = img.width / img.height
                target_ratio = target_size[0] / target_size[1]
                
                if img_ratio > target_ratio:
                    # Image is wider than target
                    new_height = img.height
                    new_width = int(target_ratio * new_height)
                    left = (img.width - new_width) // 2
                    crop_box = (left, 0, left + new_width, new_height)
                else:
                    # Image is taller than target
                    new_width = img.width
                    new_height = int(new_width / target_ratio)
                    top = (img.height - new_height) // 2
                    crop_box = (0, top, new_width, top + new_height)
                
                cropped = img.crop(crop_box)
                resized = cropped.resize(target_size, Image.Resampling.LANCZOS)
                resized.save(output_path)
                
            elif method == 'borders':
                # Maintain aspect ratio, add black borders
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create new image with black background
                new_img = Image.new("RGB", target_size, (0, 0, 0))
                
                # Calculate position to center the thumbnail
                paste_x = (target_size[0] - img.width) // 2
                paste_y = (target_size[1] - img.height) // 2
                
                # Paste the thumbnail onto the black background
                new_img.paste(img, (paste_x, paste_y))
                new_img.save(output_path)

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
            text=True,
            check=True
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
        ], capture_output=True, text=True, check=True)
        result = result.stdout.strip().split(",")
        return (int(result[0]),int(result[1]))

    @staticmethod
    def getFramerate(path:str) -> int:
        result = subprocess.run([
            "ffprobe",
            "-v", "error",
            "-select_streams", "v",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-show_entries", "stream=r_frame_rate",
            path
        ], capture_output=True, text=True, check=True)
        result = result.stdout.strip().split("/")
        return round(float(result[0])/float(result[1]))

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

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

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
    def getFontPath(font_name, extensions=None) -> None | str:
        if extensions is None:
            extensions = ['.ttf', '.otf', '.ttc']
        
        system = platform.system()
        font_dirs = []
        
        if system == "Windows":
            font_dirs = [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
            ]
        elif system == "Darwin":  # macOS
            font_dirs = [
                '/Library/Fonts/',
                '/System/Library/Fonts/',
                os.path.expanduser('~/Library/Fonts/')
            ]
        else:  # Linux and others
            font_dirs = [
                '/usr/share/fonts/',
                '/usr/local/share/fonts/',
                os.path.expanduser('~/.fonts/'),
                os.path.expanduser('~/.local/share/fonts/')
            ]
        
        # Search for font
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        file_lower = file.lower()
                        font_lower = font_name.lower()
                        
                        # Check if filename contains font name (with or without extension)
                        base_name = os.path.splitext(file_lower)[0]
                        if font_lower in base_name:
                            # Check if it's a valid font extension
                            if any(file_lower.endswith(ext) for ext in extensions):
                                full_path = os.path.join(root, file)
                                return full_path
        
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
    def bgrToHex(color_str: str, include_alpha: bool = False) -> str:
        """
        Convert BGR color string "&HAABBGGRR" to FFmpeg hex format.
        
        Args:
            color_str: Color string in format "&HAABBGGRR" where:
                    &H = hex prefix
                    AA = alpha (00=transparent, FF=opaque)
                    BB = blue component
                    GG = green component
                    RR = red component
            include_alpha: If True, returns "0xRRGGBBAA" format with alpha at end.
                        If False, returns "0xRRGGBB" format (default, alpha ignored).
        
        Returns:
            String in format "0xRRGGBB" or "0xRRGGBBAA"
        
        Examples:
            >>> bgr_to_ffmpeg_hex("&HFFA0B0C0")
            '0xC0B0A0'
            
            >>> bgr_to_ffmpeg_hex("&H80A0B0C0", include_alpha=True)
            '0xC0B0A080'
        """
        # Remove the "&H" prefix
        if not color_str.upper().startswith("&H"):
            raise ValueError(f"Invalid format: expected '&H' prefix, got {color_str}")
        
        hex_str = color_str[2:].upper()  # Remove "&H"
        
        # Validate length
        if len(hex_str) != 8:
            raise ValueError(f"Invalid length: expected 8 hex digits after &H, got {len(hex_str)}")
        
        # Parse components
        try:
            aa = hex_str[0:2]  # Alpha
            bb = hex_str[2:4]  # Blue
            gg = hex_str[4:6]  # Green
            rr = hex_str[6:8]  # Red
        except IndexError:
            raise ValueError(f"Invalid format: could not parse components from {color_str}")
        
        # Convert to FFmpeg format
        if include_alpha:
            # Format: 0xRRGGBBAA
            return f"0x{rr}{gg}{bb}{aa}"
        else:
            # Format: 0xRRGGBB (alpha ignored)
            return f"0x{rr}{gg}{bb}"

    @staticmethod
    def concatenate(paths: list[str], endPath: str, reencode=False, isTemp=True) -> None:
        """
        Concatenate multiple video files.
    
        If reencode=False, inputs must already have identical codec parameters.
        If reencode=True, each input is re-encoded to a common format (H.264, yuv420p,
        stereo AAC at 44.1 kHz) before concatenation. The temporary normalised files
        are automatically cleaned up.
    
        Args:
            paths: List of input file paths.
            endPath: Output file path.
            reencode: If True, normalise all inputs to a common format.
            isTemp: If True, endPath will be added to tempFiles for later cleanup.
        """
        # Create the concat list file
        textFile = tempFolder + os.path.splitext(os.path.basename(endPath))[0] + ".txt"
        tempFiles.append(textFile)

        if reencode:
            # Normalise each input to a common format
            normalised_paths = []
            for i, p in enumerate(paths):
                norm = f"{tempFolder}norm_{random.randint(10000,99999)}_{i}.mp4"
                subprocess.run([
                    "ffmpeg",
                    "-v", "error",
                    "-i", p,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-ac", "2",           # force stereo
                    "-ar", "44100",        # force 44.1 kHz sample rate
                    "-y",                  # overwrite if exists
                    norm
                ], check=True)
                normalised_paths.append(norm)
                tempFiles.append(norm)     # mark for cleanup

            # Write the list of normalised files
            with open(textFile, "w") as f:
                for item in normalised_paths:
                    f.write(f"file '{item}'\n")

            # Concatenate using stream copy (all files are now compatible)
            subprocess.run([
                "ffmpeg",
                "-v", "error",
                "-safe", "0",
                "-f", "concat",
                "-i", textFile,
                "-c", "copy",              # no re-encoding needed
                endPath
            ], check=True)
        else:
            # No normalisation: assume inputs are already compatible
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
            ], check=True)

        # If the output is temporary, add it to the cleanup list
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def cut(ogPath:str, begin:float, end:float, endPath:str, reencode:bool=True, roundUpOrDown:tuple[bool,bool]=(True,True), isTemp=True) -> None: #if reencode=True, the video will be reencoded so the cut will be frame-perfect. else, the video will get rounded to the nearest keyframe. set roundUpOrDown to True to add excess frames, set it to False to cut them: since it's a tuple, this applies to both begin and end time
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
            ], check=True)
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
            ], check=True)
        
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
        ], check=True)
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def imageToVideo(imagePath:str, endPath:str, duration:float, framerate:int=30, isTemp=True) -> None:
        """
        Convert a given image to a video of given duration and frame rate.
        """
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-loop", "1",
            "-i", imagePath,
            "-t", str(duration),
            "-r", str(framerate),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            endPath
        ], check=True)
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def applyVideoEffect(sourcePath:str, endPath:str, filter:str, isTemp=True) -> None:
        """
        Apply given filter effect (in standard FFmpeg notation) to a given video.
        """
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", sourcePath,
            "-vf", filter,
            "-c:a", "copy",
            endPath
        ], check=True)
        if isTemp:
            tempFiles.append(endPath)

    @staticmethod
    def overlayImage(videoPath:str, imagePath:str, endPath:str, duration:tuple[float,float]=(0,0.1), position:tuple[int,int]=(0,0), scale:float=1, center=False, isTemp=True): #duration=(begin time, end time) | position=(x,y) | scale changes the image size keeping it in proportion | if center=True the image will be centered in the video | isTemp=True will add the path to tempFiles, deleting it when clearTemp is called
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
        ], check=True)

        tempFiles.append(ovPath)

        if not matchesVideo:
            FFmpeg.concatenate(concatList,endPath,isTemp)

        if isTemp and (not endPath in tempFiles):
            tempFiles.append(endPath)

    @staticmethod
    def overlayVideo(backgroundVideo:str, foregroundVideo:str, endPath:str, chromakey:str = "&HFF00FF00", similarity:float=0.1, blend:float=0.1, isTemp=True) -> None:
        """
        Overlays a 'foregroundVideo' onto a 'backgroundVideo', saving the final result to 'endPath'.
        Will apply a chroma-key filter with the color 'chromakey' (in BGR) and apply parameters 'similarity' and 'blend' to better specify the interested area.
        """
        filter:str = f"[1:v]chromakey=color={FFmpeg.bgrToHex(chromakey)}:similarity={similarity}:blend={blend}[ckout];[0:v][ckout]overlay[out]"
        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", backgroundVideo,
            "-i", foregroundVideo,
            "-filter_complex", filter,
            "-map", "[out]",
            "-map", "0:a?", #?=makes audio optional
            "-c:a", "copy",
            endPath
        ], check=True)

        if isTemp and (not endPath in tempFiles):
            tempFiles.append(endPath)

    @staticmethod
    def addText(videoPath:str, text:str, duration:tuple[float,float], endPath:str, position:tuple[int,int]|int = (0,0), margin:int = 0,  font:str="Arial", fontSize:int=16, color:str = "&HFF000000", isTemp=True) -> None:
        """
        Add text to a video.

        Parameter "position" can either be a tuple[int,int] containing X and Y coordinates or can be one of the following ints:
        - '1' for top left
        - '2' for top center      Visualization: +-------------+
        - '3' for top right                      | 1    2    3 |
        - '4' for middle left                    | 4    5    6 |
        - '5' for middle center                  | 7    8    9 |
        - '6' for middle right                   +-------------+
        - '7' for bottom left
        - '8' for bottom center
        - '9' for bottom right

        Parameter "margin" (int, representing pixels) is only used when position isn't tuple[int,int]. It defines an offset from borders.

        Parameter "duration" is tuple[float,float] of (begin time, end time)

        Parameter "color" is in BGR, formatted &HAABBGGRR, &H=hex, AA=alpha(FF is opaque)
        """
        coordsExpression:tuple[str,str] = ("0", "0")
        if type(position) == int:
            if position not in range(1, 10):
                raise ValueError(f"Position must be 1-9 or tuple, got {position}")
            expX:str = "0"
            expY:str = "0"
            #find expression to use for X coords
            match position:
                case 1 | 4 | 7:
                    expX = f"{margin}"
                case 2 | 5 | 8:
                    expX = "(w-text_w)/2"
                case 3 | 6 | 9:
                    expX = f"(w-text_w)-{margin}"
            #find expression to use for Y coords
            match position:
                case 1 | 2 | 3:
                    expY = f"{margin}"
                case 4 | 5 | 6:
                    expY = "(h-text_h)/2"
                case 7 | 8 | 9:
                    expY = f"(h-text_h)-{margin}"
            #put them together
            coordsExpression = (expX, expY)
        elif type(position) == tuple[int,int]:
            coordsExpression:tuple[str,str] = (str(position[0]), str(position[1]))

        if os.path.isfile(font):
            fontFile = font
        else:
            fontFile = FFmpeg.getFontPath(font)
            if fontFile is None:
                raise LookupError(f"Unable to find path for default font '{font}'.")

        escapedText = text.replace("'", "'\"'\"'")

        subprocess.run([
            "ffmpeg",
            "-v", "error",
            "-i", videoPath,
            "-vf", f"drawtext=fontfile='{fontFile}':text='{escapedText}':x={coordsExpression[0]}:y={coordsExpression[1]}:fontsize={fontSize}:fontcolor={FFmpeg.bgrToHex(color)}:enable='between(t,{duration[0]},{duration[1]})'",
            "-c:a", "copy",
            endPath
        ], check=True) 

        if isTemp:
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
        ], check=True)
        if isTemp:
            tempFiles.append(endPath)

