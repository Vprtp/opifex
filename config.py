# CONFIGURATIONS CHANGES TAKE EFFECT ONLY AFTER REBOOTING THE PROGRAM
# DO NOT MESS WITH THIS FILE IF YOU DON'T KNOW WHAT YOU'RE DOING

import os
p = os.path.abspath(__file__).replace(os.path.basename(__file__),"") #DO NOT change this. it's used to detect the script directory

#OPIFEX CONFIGS
windowSize:tuple[int,int] = (1225,800)
manual:str = p+"README.html"
icon:str = p+"source/img/logo.png"
style:str = p+"source/qt/light.qss" #options: "source/qt/light.qss", "source/qt/dark.qss", "source/qt/none.qss"
tempFolder:str = p+"temp/"
sourceFolder:str = p+"source/"
outputFolder:str = p+"generated/"

#DEFAULT MODULES CONFIGS

class Theme: #DO NOT change this. it's used to define other variables later
    def __init__(self, color:str="&HFF000000", font:str="Arial", fontSize:int=16, alignment:int=5, contourWidth:int=0, countourColor:str=""):
        """
        Theme class (mainly meant for FFmpeg use cases, but is fine for everything)
        Parameters:
        - color (str): font color, formatted &HAABBGGRR, &H=hex, AA=alpha(FF is opaque), it's in in BGR format, not RGB
        - font (str): font to be used (can be either a path to a font file or an already installed font)
        - fontSize (int): size (in pixels) for the font
        - alignment (int): text alignment in ASS subtitle standard notation (alignment=5 is center)
        - contourWidth (int): width (in pixels) for the font contour (countourWidth=0 means no contour)
        - contourColor (str): countour color, formatted &HAABBGGRR, &H=hex, AA=alpha(FF is transparent), it's in in BGR format, not RGB
        """
        self.color = color
        self.font = font
        self.fontSize = fontSize
        self.alignment= alignment
        self.contourWidth = contourWidth
        self.contourColor = countourColor

accountName:str = "Fallback account name"
subtitlesTheme:Theme = Theme(color="&H0000E6FF", 
                         font=p+"source/font/SpecialGothicExpandedOne-Regular.ttf",
                         fontSize=80,
                         countourColor="&H00000000", 
                         contourWidth=10
                         )
newsTitleTheme:Theme = Theme(color="&H00B7B7FF",
                             font=p+"source/font/Ubuntu-Bold.ttf",
                             fontSize=140,
                             alignment=4
                            )

videoOutputFolder:str = outputFolder
audioOutputPath:str = outputFolder+"voice/{time}/{fileName}.wav"

piperLocation:str = sourceFolder+"piper/piper"
piperModel:str = sourceFolder+"voice/en_US-lessac-medium.onnx"
alignerDict:str = sourceFolder+"aligner/english_us_mfa.dict"
alignerModel:str = sourceFolder+"aligner/english_mfa"
videoPool:list[str] = [sourceFolder+"video/background-gta01.mp4", sourceFolder+"video/background-gta02.mp4", sourceFolder+"video/background-mc01.mp4", sourceFolder+"video/background-mc02.mp4", sourceFolder+"video/background-msc01.mp4", sourceFolder+"video/background-msc02.mp4"]
dingSound:str = sourceFolder+"audio/ding.wav"

titleHtmlTemplate:str = sourceFolder+"web/reddit.html"
newsHtmlTemplate:str = sourceFolder+"web/news.html"
noMediaHtmlTemplate:str = sourceFolder+"web/noimage.html"

imageSearchProvider:str = "https://www.ecosia.org/images?q={terms}" #url for image search provider. ecosia is used because downloading images with it is more straightforward

newsTitleBackgroundVideo:str = f"{sourceFolder}/video/globe-red.mp4"
newsTitleSong:str = f"{sourceFolder}/audio/news-title-music.wav"
