import feedparser
import requests
import time
from random import choice
from trafilatura import extract
from basemodule import BaseModule, ModuleResultType

#list of possible user agent headers to choose from
userAgents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
              "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
              "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
              "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Edge/79.0.1451.30 Safari/537.36"]

def getRandomHeaders() -> dict[str]:
    return {'User-Agent': choice(userAgents)}

def get(url:str, fullArticle:bool) -> dict:
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
                    },
                    {<second entry>}, 
                    {<third entry>}, 
                    {<etc>}
                  ]
    }
    
    :param url: URL to the feed
    :type url: str
    :param fullArticle: Whether or not to download the full article by following the link given in each RSS entry
    :type fullArticle: bool
    """
    feed = feedparser.parse(url)
    entries:list[dict] = []

    tempentry:dict = {}
    article:str = ""
    for entry in feed.entries:
        tempentry.clear()

        tempentry["title"] = entry.title
        tempentry["author"] = entry.author
        tempentry["link"] = entry.link
        tempentry["time"] = int(time.mktime(entry.published_parsed))
        if fullArticle:
            article = requests.get(entry.link, headers=getRandomHeaders()).text
            tempentry["content"] = extract(article)
        else:
            tempentry["content"] = extract(entry.summary)
        
        entries.append(tempentry)
    
    val:dict = {
        "feedtitle" : feed.feed.title,
        "feeddesc" : feed.feed.description,
        "feedlink" : feed.feed.link,
        "entries" : entries
    }
    return val

class RSS(BaseModule):
    def __init__(self):
        self.name = "RSS"
        self.description = """
        Module to fetch info from an RSS feed and its individual articles.
        
        Parameters:
        -feedURL: URL to the RSS feed
        -getFullArticle: Whether or not to download the full article by following the link given in each RSS entry

        Returns dict in this format, containing each entry in the "entries" key:
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
                        },
                        {<second entry>}, 
                        {<third entry>}, 
                        {<etc>}
                    ]
        }
        """
        self.requiredArgs = [("feedURL",str),("getFullArticle",bool)]
        self.returnedDataTypes = [("feedInfo",dict)]
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            val = get(kwargs["feedURL"],kwargs["getFullArticle"])
            return ModuleResultType(None,{"feedInfo":val})
        except Exception as e:
            return ModuleResultType(e,{})

