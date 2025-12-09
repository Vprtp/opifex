import unshortenURL
import reddit
from basemodule import BaseModule, ModuleResultType
import traceback
import simple_video_generator as svideo

def generate(url:str, commsOrDesc:bool, accountName:str):
    print("REDDIT VIDEO GENERATOR")
    url = unshortenURL.getUrl(url)
    a = reddit.getJSON(url)
    title:str = reddit.getTitle(a)
    paths:list[str] = []
    content:dict[str,str] = {}
    print(f"Title: '{title}' Upvotes: {reddit.getUpvotes(a)} Mode: {"comments" if commsOrDesc else "description"}")
    if commsOrDesc:
        comments:list[str] = reddit.getComments(a)
        for i in range(len(comments)):
            print(f"COMMENT {i}:\n{comments[i]}")
            content[f"{i+1} - {title}"] = comments[i]
    else:
        desc:str = reddit.getDescription(a)
        content[title] = desc
    paths = svideo.generate(content, accountName, verboseName=False)
    return paths

class RedditVideoGenerator(BaseModule):
    def __init__(self):
        self.name = "RedditVideoGenerator"
        self.description = "Module that generates a video, or multiple videos, based on the content contained in a given Reddit post. Returns paths to the generated videos (list of size 1 when only one video is generated)\n\nParameters:\n-url: URL to the Reddit post\n-commentsOrDesc: whether to generate multiple videos based on the comments (True) or to generate one video from the post's description (False)\n-accountName: credits that will be shown in the video"
        self.requiredArgs = [("url",str),("commentsOrDesc",bool),("accountName",str)]
        self.returnedDataTypes = [("paths",list[str])]
        self.dependencies = ["Reddit","SimpleVideoGenerator","URLunshortener"]
    
    def execute(self, version:str, **kwargs):
        try:
            paths:list[str]= generate(kwargs["url"],kwargs["commentsOrDesc"],kwargs["accountName"])
            return ModuleResultType(None,{"paths":paths})
        except Exception as e:
            print(traceback.format_exc())
            return ModuleResultType(e,{})
