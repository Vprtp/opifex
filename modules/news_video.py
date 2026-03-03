import time
import shutil
from pathlib import Path
import record
import tts
from basemodule import BaseModule, ModuleResultType
from lib.ffmpeghandler import *
import config

class Article:
    def __init__(self, title:str, text:str, images:list[str], source:str, publishTime:int):
        """
        Parameters:
        - title: Title of the article (or very short summary)
        - text: The article itself
        - images: List of paths of images related to the article
        - source: Name of the author or newspaper the article comes from
        - publishTime: Unix timestamp for when the article was published
        """
        self.title:str = title
        self.text:str = text
        self.images:list[str] = images
        self.source:str = source
        self.publishTime:int = publishTime

newsTempNum:int = 0
def genTempPath(extension:str) -> str:
    """
    Generates a file name for a temporary file with the following formatting:
        [TEMPORARY DIRECTORY PATH]/news_[LAST 5 DIGITS OF CURRENT UNIX TIMESTAMP]-[NUMBER INCREASING FROM 0 FOR EACH CALL].[extension]
    """
    global newsTempNum
    path:str = f"{config.tempFolder}news_{str(int(time.time()))[-5:]}-{newsTempNum}.{extension}"
    newsTempNum += 1
    return path 

def generate(newsName:str, articles:list[Article], endPath:str, showTitle:bool=True, graphicModel:str=config.newsHtmlTemplate, titleBgVideo:str=config.newsTitleBackgroundVideo, titleBgAudio:str=config.newsTitleSong, titleTheme:config.Theme=config.newsTitleTheme, fadeEffect:str="fade=t=in:st=0:d={fadeDuration},fade=t=out:st={imgDurationMinusFadeDuration}:d={fadeDuration}") -> None:
    """
    Generates a News report-like video based on given parameters:
    - newsName: name of your news broadcast
    - articles: list of Articles that will be included in the video
    - endPath: destination of the generated video
    - showTitle: whether or not to show the title you gave to your news broadcast
    - graphicModel
    """
    print("NEWS VIDEO GENERATOR") 
    #this will get changed to the title's background video size later if a title is generated
    newsSize:tuple[int,int]=(1920,1080) 
    newsFps:int = 30
    
    print("Generating title video...")
    #generate title
    titlePath:str = genTempPath("mp4")
    if showTitle:
        titleNoAudio:str = genTempPath("mp4")
        bgVideoDuration:float = FFmpeg.getLength(titleBgVideo)
        bgVideoSize:tuple[int,int] = FFmpeg.getSize(titleBgVideo)
        bgVideoFramerate:int = FFmpeg.getFramerate(titleBgVideo)
        newsSize = bgVideoSize
        newsFps = bgVideoFramerate
        FFmpeg.addText(titleBgVideo,newsName,(0.0, bgVideoDuration), titleNoAudio, position=titleTheme.alignment, margin=int(bgVideoSize[0]/20), font=titleTheme.font, fontSize=titleTheme.fontSize, color=titleTheme.color)
        FFmpeg.addAudioToVideo(titleBgAudio, titleNoAudio, titlePath)

    #generate individual article videos
    articleTitles:list[str] = [art.title for art in articles]
    articleVideoPaths:list[str] = []
    for article in articles:
        print(f"Generating video for article '{article.title}'. This may take several minutes, please be patient...")
        #generate tts
        ttsPath:str = tts.generate(article.text)
        ttsLenght:float = FFmpeg.getLength(ttsPath)
        #get list of all article titles except for this one
        otherArticles:list[str] = articleTitles
        otherArticles.remove(article.title)
        #generate the news overlay
        overlayPath = record.process_html_to_video(graphicModel, 
                                                   data={"article_time":time.strftime('%d/%m %H:%M', time.localtime(article.publishTime)),
                                                         "article_title":article.title,
                                                         "article_source":article.source,
                                                         "other_articles":" | ".join(otherArticles)},
                                                   window_size=newsSize,
                                                   duration=ttsLenght,
                                                   fps=newsFps)

        #resize images
        images:list[str] = []
        for img in article.images:
            imgOld:str = img
            ext = imgOld.split(".")[-1]
            img:str = genTempPath(ext)
            ImageProcessing.resize(imgOld, img, newsSize, method="cut")
            images.append(img)

        #generate video of background images
        singularImageLenght:float = ttsLenght/len(images)
        imageVideoPaths:list[str] = [genTempPath("mp4") for img in images]
        for i in range(len(images)): #generate single videos from images
            FFmpeg.imageToVideo(images[i], imageVideoPaths[i], singularImageLenght, framerate=newsFps)
        fadeDuration:float = 0.8
        if singularImageLenght <= 8.0:
            fadeDuration = singularImageLenght/10
        fadedImageVideoPaths:list[str] = [genTempPath("mp4") for img in images]
        for i in range(len(imageVideoPaths)): #generate single videos with fade duration
            effect:str = fadeEffect.format(imgDuration=singularImageLenght, fadeDuration=fadeDuration, imgDurationMinusFadeDuration=singularImageLenght-fadeDuration)
            FFmpeg.applyVideoEffect(imageVideoPaths[i], fadedImageVideoPaths[i], effect)
        bgVideo:str = genTempPath("mp4")
        FFmpeg.concatenate(fadedImageVideoPaths, bgVideo, reencode=True) #create final background video for the article
        #overlay news to background and add audio
        articlePathNoAudio:str = genTempPath("mp4")
        FFmpeg.overlayVideo(bgVideo, overlayPath, articlePathNoAudio)
        articlePath:str = genTempPath("mp4")
        FFmpeg.addAudioToVideo(ttsPath, articlePathNoAudio, articlePath)
        articleVideoPaths.append(articlePath)

    #apply fade effect to individual article videos
    print("Applying effects...")
    fadedArticleVideos:list[str] = [genTempPath("mp4") for vid in articleVideoPaths]
    fadeDuration:float = 1.0
    for i in range(len(articleVideoPaths)):
        vidLenght:float = FFmpeg.getLength(articleVideoPaths[i])
        effect:str = fadeEffect.format(imgDuration=vidLenght, fadeDuration=fadeDuration, imgDurationMinusFadeDuration=vidLenght-fadeDuration)
        FFmpeg.applyVideoEffect(articleVideoPaths[i], fadedArticleVideos[i], effect)

    #concatenate everything
    print("Concatenating...")
    articlesFull = genTempPath("mp4")
    FFmpeg.concatenate(fadedArticleVideos,articlesFull,reencode=True)
    if showTitle:
        FFmpeg.concatenate([titlePath, articlesFull], endPath, reencode=True, isTemp=False)
    else:
        shutil.copyfile(articlesFull,endPath)
    print("Done!")
    FFmpeg.clearTemp()

class NewsVideoGenerator(BaseModule):
    def __init__(self):
        self.name = "NewsVideoGenerator"
        self.description = "Module that generates a news-broadcast style video.\n\nParameters:\n-broadcastName: Name for your news 'broadcast', which will be shown at the beginning of the video\n-articles: List of articles that will be shown, each with the tuple format (ARTICLE TITLE-str, ARTICLE TEXT-str, IMAGES USED IN THE VIDEO-list[Path], ARTICLE SOURCE-str, PUBLISH TIME IN UNIX TIMESTAMP-int)\n-destination: Path to the video that will be generated"
        self.requiredArgs = [("broadcastName",str), ("articles",list[tuple[str, str, list[Path], str, int]]), ("destination", Path)]
        self.returnedDataTypes = []
        self.dependencies = ["RecordPage", "TTS"]
    
    def execute(self, version:str, **kwargs):
        try:
            #convert composite generic type to Article
            articles:list[Article] = []
            for art in kwargs["articles"]:
                articles.append(Article(title=art[0],
                                        text=art[1],
                                        images=[str(x.absolute()) for x in art[2]],
                                        source=art[3],
                                        publishTime=art[4]))
            #generate video
            generate(kwargs["broadcastName"], articles, kwargs["destination"])
            return ModuleResultType(None,{})
        except Exception as e:
            return ModuleResultType(e,{})
