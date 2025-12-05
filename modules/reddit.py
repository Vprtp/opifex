import requests
from basemodule import BaseModule, ModuleResultType

url:str = "{url}.json" #Requested URL

upvotesMin:float = 0.1 #Fraction of comment upvotes required to pass the filter, compared to the original post's upvotes. For example, if upvotesMin = 0.5 and the original post has 100 upvotes, comments must have at least 50 upvotes to be considered.
wordsMin:int = 75 #Minimum words in the comment to be considered.
checkMax:int = 64 #Highest index of comment to check. The higher, the slower the process, but more comments will be considered

titleJSONPath:list = [0,"data","children",0,"data","title"] #Path to reach the text title of the thread from the recieved JSON.
descriptionJSONPath:list = [0,"data","children",0,"data","selftext"] #Path to reach the text description of the thread from the recieved JSON.
postUpvotesPath:list = [0,"data","children",0,"data","ups"] #Path to reach the upvotes value of the thread from the recieved JSON.
commentListJSONPath:list = [1,"data","children"] #Path to reach the list of all thread comments from the recieved JSON.
commentUpvotesPath:list = ["data","ups"] #Path to reach the comment upvotes value starting from the specific comment in the list
commentBodyPath:list = ["data","body"] #Path to reach the comment body text starting from the specific comment in the list

def getJSON(originalURL:str, url:str=url):
    response = requests.get(url.format(url = originalURL))
    response = response.json()
    if "error" in response:
        raise Exception(f"Error from Reddit: {response["error"]} - {response["message"]}")
    else:
        return response

def getTitle(threadJSON, path:list=titleJSONPath) -> str:
    title = threadJSON
    for i in range(len(path)):
        title = title[path[i]]
    return title

def getUpvotes(threadJSON, path:list=postUpvotesPath) -> int:
    ups = threadJSON
    for i in range(len(path)):
        ups = ups[path[i]]
    return ups

def getDescription(threadJSON, path:list=descriptionJSONPath) -> int:
    description = threadJSON
    for i in range(len(path)):
        description = description[path[i]]
    return description

def getComments(threadJSON, upMin:float=upvotesMin, wMin:int=wordsMin, check:int=checkMax, listPath:list=commentListJSONPath, upPath:list=commentUpvotesPath, bodyPath:list=commentBodyPath):
    textsList:list[str] = []
    threadUpvotes:int = getUpvotes(threadJSON)
    commentsList = threadJSON
    for i in range(len(listPath)):
        commentsList = commentsList[listPath[i]]
    for i in range(check):
        if i < len(commentsList)-1: #-1 added because the last in the list theorically is always the "more" item
            ups = commentsList[i]
            for j in range(len(upPath)):
                ups = ups[upPath[j]]
            if ups >= (upMin*threadUpvotes):
                body = commentsList[i]
                for j in range(len(bodyPath)):
                    body = body[bodyPath[j]]
                wCount:int = len(body.split())
                if wCount >= wMin:
                    textsList.append(body)
    return textsList
    
class Reddit(BaseModule):
    def __init__(self):
        self.name = "Reddit"
        self.description = "Module for fetching reddit posts.\n\nParameters:\n-url: (Verbose, not shortened) URL to the desired Reddit post\n-upvotesMin: Fraction of comment upvotes required to pass the filter, compared to the original post's upvotes. For example, if upvotesMin = 0.5 and the original post has 100 upvotes, comments must have at least 50 upvotes to be considered.\n-wordsMin: Minimum words in the comment to be considered.\n-checkMax: Highest index of comment to check. The higher, the slower the process, but more comments will be considered\n\nReturns:\n-title: Title of the post\n-description: Description of the post\n-upvotes: Upvotes of the post\n-comments: List of the filtered comments from the comment section, given earlier parameters"
        self.requiredArgs = [("url",str),("upvotesMin",float),("wordsMin",int),("checkMax",int)]
        self.returnedDataTypes = [("title",str),("description",str),("upvotes",int),("comments",list[str])]
        self.dependencies = ["Screenshot"]
    
    def execute(self, version:str, **kwargs):
        try:
            json = getJSON(kwargs["url"])
            title:str = getTitle(json)
            ups:int = getUpvotes(json)
            desc:str = getDescription(json)
            comments:list[str] = getComments(json, upMin=kwargs["upvotesMin"], wMin=kwargs["wordsMin"], check=kwargs["checkMax"])

            return ModuleResultType(None,{"title":title,"description":desc,"upvotes":ups,"comments":comments})
        except Exception as e:
            return ModuleResultType(e,{})