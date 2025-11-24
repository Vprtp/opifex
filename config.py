# CONFIGURATIONS CHANGES TAKE EFFECT ONLY AFTER REBOOTING THE PROGRAM
# DO NOT MESS WITH THIS FILE IF YOU DON'T KNOW WHAT YOU'RE DOING


# WARNING: THIS PROGRAM CURRENTLY ONLY WORKS ON LINUX

#IGNORE FROM HERE
import os
p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")
class Theme:
    def __init__(self, color:str="&000000FF", font:str="Arial", fontSize:int=16, alignment:int=5, contourWidth:int=0, countourColor:str=None): #alignment and color are in ASS subtitle standard notation (ex. alignment=5 is center, color is formatted &HAABBGGRR, &H=hex, AA=alpha(FF is opaque), then color is in BGR format, not RGB)
        self.color = color
        self.font = font
        self.fontSize = fontSize
        self.alignment= alignment
        self.contourWidth = contourWidth
        self.contourColor = countourColor
#TO HERE
#This is just used to configure other settings it should NOT be modified

windowSize:tuple[int,int] = (1000,800)
manual:str = p+"README.html"

accountName:str = "@Vprtp"
subtitlesTheme:Theme = Theme(color="&H0000E6FF", 
                         font=p+"source/font/SpecialGothicExpandedOne-Regular.ttf",
                         fontSize=80,
                         countourColor="&H00000000", 
                         contourWidth=10
                         )

outputFolder:str = p+"generated/"
videoOutputFolder:str = outputFolder+"video/"
audioOutputPath:str = outputFolder+"voice/{time}/{fileName}.wav"

sourceFolder:str = p+"source/"
piperLocation:str = sourceFolder+"piper/piper"
piperModel:str = sourceFolder+"voice/en_US-lessac-medium.onnx"
alignerDict:str = sourceFolder+"aligner/english_us_mfa.dict"
alignerModel:str = sourceFolder+"aligner/english_mfa"
videoPool:list[str] = [sourceFolder+"video/background-gta01.mp4", sourceFolder+"video/background-gta02.mp4", sourceFolder+"video/background-mc01.mp4", sourceFolder+"video/background-mc02.mp4", sourceFolder+"video/background-msc01.mp4", sourceFolder+"video/background-msc02.mp4"]
dingSound:str = sourceFolder+"audio/ding.wav"
titleHtmlTemplate:str = sourceFolder+"img/reddit.html"
icon:str = sourceFolder+"img/logo.png"

tempFolder:str = p+"temp/"
