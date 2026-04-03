import feedparser
import requests
from calendar import timegm
from random import choice
from trafilatura import bare_extraction
import lib.textprocessing as tp
from basemodule import BaseModule, ModuleResultType

#list of possible user agent headers to choose from
userAgents:list[str] = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
              "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
              "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
              "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Edge/79.0.1451.30 Safari/537.36"]

minimumChars:int = 80 #minimum number of characters for an article to be considered as such

#NOTE that these patterns were noticed by personal observation of newspapers I regularly read, thus they are very limited in number. Any suggestion or improvement is more than welcome.
#list of patterns in strings which suggest that the whole sentence might be useless junk, case-insensitive so must be written in lowercase
uselessSentencePatterns:list[str] = [
    "play-arrow", "recommended stories", "- list", "published on",
    "first appeared on",
    "scrivici a:", "scrivici per correzioni",
    "read more:"
]
#list of patterns that suggest the whole article is junk, case-insensitive so must be written in lowercase
uselessArticlePatterns:list[str] = [
    "this cookie, set by cloudflare", "questo cookie è impostato dal plugin", "questo è un articolo di approfondimento riservato ai nostri abbonati", 
    "l'ascolto è riservato agli abbonati premium", "la guida allo shopping del gruppo gedi",
    "mattina24 - puntata", "pomeriggio24 - puntata"
]

def getRandomHeaders() -> dict[str,str]:
    return {'User-Agent': choice(userAgents)}

def filterArticleText(text:str, sentencePatterns:list[str]=uselessSentencePatterns, articlePatterns:list[str]=uselessArticlePatterns, minChars:int=minimumChars) -> str:
    """
    Checks for common patterns of useless parts of articles in the given text and removes them. Returns the filtered string.
    If the whole article gets flagged as useless, an empty string will be returned.
    """
    #check if the whole article is useless
    for pat in articlePatterns:
        if pat in text.lower():
            return ""
    #find useless sentences and remove them
    for pat in sentencePatterns:
        if pat in text.lower():
            indices:list[int] = tp.find(text.lower(), pat)
            text = tp.deleteMultipleSentences(text, indices)
    
    #consider the article as empty if it's too small
    if len(text) >= minChars:
        return text
    else:
        return ""

def get(url:str, fullArticle:bool, smartFilter:bool) -> dict:
    """
    Get all info from a given RSS feed. Returns dict in this format, containing each entry in the "entries" key:
    {
        feedtitle : <Title of the requested RSS feed, string>
        feeddesc : <Description of the requested RSS feed, string>
        feedlink : <Link to the requested RSS feed, string>
        entries : [
                    {
                        title : <Title to this entry; str>
                        author : <Name of the author of the entry; str>
                        link : <Link to this entry; str>
                        time : <Time when this article was published, in Unix timestamp; int>
                        content : <Entry content, which will be the summary, if fullArticle=false, or the fetched article, if fullArticle=true; str>
                        media : <List of URLs pointing to media files extracted from article, only if fullArticle=True>
                    },
                    {<second entry>}, 
                    {<third entry>}, 
                    {<etc>}
                  ]
    }
    
    url-(str): URL to the feed
    fullArticle-(bool): Whether or not to download the full article by following the link given in each RSS entry
    smartFilter-(bool): Wheter or not to filter out articles or parts of articles based on patterns that suggest it could be junk info (ex. automated messages telling to accept cookies or empty articles)
    """
    feed = feedparser.parse(url)
    if feed.bozo: #raise an exception if fetching the feed failed
        raise Exception(f"Feedparser error: {feed.bozo_exception}")
    entries:list[dict] = []

    tempentry:dict = {}
    feedLink:str = feed.feed.link
    for entry in feed.entries:
        tempentry = {}

        tempentry["title"] = getattr(entry, "title", "No title")
        tempentry["author"] = getattr(entry, "author", "Unknown author")
        tempentry["link"] = getattr(entry, "link", "No URL")
        tempentry["time"] = int(timegm(getattr(entry, "published_parsed", (2000, 1, 1, 0, 0, 0, 0, 0, 0)))) #just to clarify: this thing gets the unix timestamp from entry.published_parsed if it exists, else it returns the timestamp for Jan 1st 2000 at midnight
        if fullArticle:
            resp = requests.get(str(entry.link), headers=getRandomHeaders())
            resp.raise_for_status() #catch http errors
            html = resp.text

            #extract structured data including images
            extracted:dict = bare_extraction(html, url=str(entry.link), include_images=True, as_dict=True)
            #handle different return types (dict in older versions, Document in newer ones)
            data:tuple[list[str],str] = tp.findURLs(extracted['text']) #assume it's already a dict

            #make all urls absolute
            imgs:list[str] = []
            for img in data[0]:
                if tp.isAbsoluteURL(img):
                    imgs.append(img)
                else:
                    imgs.append(tp.joinWithSeparator(feedLink, img, '/'))
           
            text:str = ""
            if smartFilter:
                text = filterArticleText(tp.cleanText(data[1]))
            else:
                text = tp.cleanText(data[1])

            if text == "": #skip the article entirely if it's empty
                continue


            tempentry["content"] = text
            tempentry["media"] = tp.isolateMediaURLs(imgs) #list of media URLs, empty list if none
        else:
            tempentry["content"] = tp.cleanText(getattr(entry, "summary", "No summary"))
            tempentry["media"] = []
        
        entries.append(tempentry)

    val:dict = {
        "feedtitle" : feed.feed.title,
        "feeddesc" : feed.feed.description,
        "feedlink" : feedLink,
        "entries" : entries
    }
    return val

class RSS(BaseModule):
    def __init__(self):
        self.name = "RSS"
        self.description = "Module to fetch info from an RSS feed and its individual articles.\n\nParameters:\n-feedURL: URL to the RSS feed\n-getFullArticle: Whether or not to download the full article by following the link given in each RSS entry\n-smartFilter: Wheter or not to filter out articles or parts of articles based on patterns that suggest it could be junk info (ex. automated messages telling to accept cookies or empty articles) [NOT 100% CORRECT! USE WITH CAUTION!]\n\nReturns dict in this format, containing each entry in the 'entries' key:\n{\n\tfeedtitle : <Title of the requested RSS feed, string>\n\tfeeddesc : <Description of the requested RSS feed, string>\n\tfeedlink : <Link to the requested RSS feed, string>\n\tentries : [\n\t\t\t{\n\t\t\t\ttitle : <Title to this entry; str>\n\t\t\t\tauthor : <Name of the author of the entry; str>\n\t\t\t\tlink : <Link to this entry; str>\n\t\t\t\ttime : <Time when this article was published, in Unix timestamp; int>\n\t\t\t\tcontent : <Entry content, which will be the summary, if fullArticle=false, or the fetched article, if fullArticle=true; str>\n\t\t\t\tmedia: <List of URLs to each media file contained in the downloaded article (only for fullArticle=true, else it's empty); list[str]>\n\t\t\t\t},\n\t\t\t{<second entry>}, \n\t\t\t{<third entry>}, \n\t\t\t{<etc>}\n\t\t]\n}"
        self.requiredArgs = [("feedURL",str),("getFullArticle",bool),("smartFilter",bool)]
        self.returnedDataTypes = [("feedInfo",dict)]
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            val = get(kwargs["feedURL"],kwargs["getFullArticle"],kwargs["smartFilter"])
            return ModuleResultType(None,{"feedInfo":val})
        except Exception as e:
            return ModuleResultType(e,{})

