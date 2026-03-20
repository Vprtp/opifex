import rss
import news_video
from image_finder import downloadImage
from lib.textprocessing import oneLiner
import config
import time
from pathlib import Path
from basemodule import BaseModule, ModuleResultType

def buildIndexMap(list_a, list_b) -> list[int]:
    """
    Returns a list `mapping` where mapping[i] is:
        - the index in list_b if list_a[i] is present in list_b,
        - -1 if list_a[i] was removed.
    Assumes list_b is a subsequence of list_a (order preserved).
    """
    mapping = [-1] * len(list_a)
    j = 0  # pointer for list_b
    for i, item in enumerate(list_a):
        if j < len(list_b) and item == list_b[j]:
            mapping[i] = j
            j += 1
        # else: item was removed, mapping[i] stays None
    return mapping

def entryToArticle(entry:dict, feedTitle:str, mediaDir:str=config.tempFolder) -> news_video.Article:
    """
    Convert an RSS module-style entry into a news_video.Article type.
    Automatically downloads all media and replaces newlines with spaces.
    """
    return news_video.Article(entry["title"], oneLiner(entry["content"]), fetchImages(entry["media"], saveDir=mediaDir), feedTitle, entry["time"])

def fetchImages(urls:list[str], saveDir:str=config.tempFolder) -> list[str]:
    """
    Download images from given URLs. Returns paths to all downloaded images.
    """
    paths:list[str] = []
    for url in urls:
        try:
            paths.append(downloadImage(url, saveDir))
        except:
            print(f"Failed to download '{url}'.")
    return paths

def fetchRSS(rssUrl:str) -> tuple[dict,dict]:
    """
    Fetches given rssUrl twice, first with fullArticle=False and smartFilter=False, then another time with both of them set to true.
    Returns a tuple where the first item is the result of the first fetch, and the second is the result of the latter.
    """
    return (rss.get(rssUrl, fullArticle=False, smartFilter=False), rss.get(rssUrl, fullArticle=True, smartFilter=True))

def extractArticles(feeds:tuple[dict,dict], quickArticles:bool=False) -> list[news_video.Article]:
    """
    Formats articles from the given feeds into a list of type Article, but before that the fetched results are compared and combined
    to ensure a better result, and all images from entries will be downloaded. 
    If quickArticles is set to True, this initial step is skipped and only the first feed is used.
    """
    articles:list[news_video.Article] = []
    feedName:str = feeds[0]["feedtitle"]
    if quickArticles:
        articles = [entryToArticle(art, feedName) for art in feeds[0]["entries"]]
    else:
        firstFeedArts:list[dict] = feeds[0]["entries"]
        secondFeedArts:list[dict] = feeds[1]["entries"]
        #this title comparison is necessary because there might be an offset between the two (caused by removed junk articles)
        mappedArts:list[int] = buildIndexMap([art["title"] for art in firstFeedArts], [art["title"] for art in secondFeedArts]) #compare list of titles in first feed to list of titles in second feed to create a map
        #compare and append each article
        for i in range(len(firstFeedArts)):
            secIndex:int = mappedArts[i] #corresponding index of the article in the second feed
            if secIndex == -1: #which means that the article is not in the second feed
                articles.append(entryToArticle(firstFeedArts[i], feedName))
            else:
                if len(secondFeedArts[secIndex]["media"]) > 0:
                    firstFeedArts[i]["media"] = secondFeedArts[secIndex]["media"]
                art:news_video.Article = entryToArticle(firstFeedArts[i], feedName)
                if len(art.text) <= len(secondFeedArts[secIndex]["content"]):
                    art.text = secondFeedArts[secIndex]["content"]
                articles.append(art)
    return articles

def generate(newsName:str, rssUrl:str, quickFetch:bool=False, destDir:str = config.videoOutputFolder) -> str:
    """
    Wrapper function for this module. Returns the generated video path.
    """
    destination:str = f"{destDir}{int(time.time())}.mp4"
    print("RSS VIDEO GENERATOR\nFetching RSS...")
    news_video.generate(newsName,
                        extractArticles(fetchRSS(rssUrl), quickArticles=quickFetch), #fetch articles from RSS and convert them to Article
                        destination)
    return destination

class RSSVideoGenerator(BaseModule):
    def __init__(self):
        self.name = "RSSVideoGenerator"
        self.description = "Module that generates a news-broadcast style video from a given RSS feed. Returns the path to the generated video.\n\nParameters:\n-broadcastName: Name for your news 'broadcast', which will be shown at the beginning of the video\n-url: URL of the RSS feed where articles will be fetched from\n-quickFetch: Avoid fetching individual articles from their web page for further information, which will make processing quicker and the video shorter but might lack images and be too short"
        self.requiredArgs = [("broadcastName",str),("url",str),("quickFetch",bool)]
        self.returnedDataTypes = [("destination",Path)]
        self.dependencies = ["RSS", "NewsVideoGenerator", "ImageFinder"]
    
    def execute(self, version:str, **kwargs):
        try:
            destination:str = generate(kwargs["broadcastName"], kwargs["url"], quickFetch=kwargs["quickFetch"])
            return ModuleResultType(None,{"destination":Path(destination)})
        except Exception as e:
            return ModuleResultType(e,{})
