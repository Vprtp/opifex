import requests

url:str = "{url}.json" #Requested URL

upvotesMin:float = 0.1 #Fraction of comment upvotes required to pass the filter, compared to the original post's upvotes. For example, if upvotesMin = 0.5 and the original post has 100 upvotes, comments must have at least 50 upvotes to be considered.
wordsMin:int = 75 #Minimum words in the comment to be considered.
checkMax:int = 64 #Highest index of comment to check. The higher, the slower the process, but more comments will be considered

titleJSONPath:list = [0,"data","children",0,"data","title"] #Path to reach the text title of the thread from the recieved JSON.
postUpvotesPath:list = [0,"data","children",0,"data","ups"] #Path to reach the upvotes value of the thread from the recieved JSON.
commentListJSONPath:list = [1,"data","children"] #Path to reach the list of all thread comments from the recieved JSON.
commentUpvotesPath:list = ["data","ups"] #Path to reach the comment upvotes value starting from the specific comment in the list
commentBodyPath:list = ["data","body"] #Path to reach the comment body text starting from the specific comment in the list

def getJSON(originalURL:str, url:str=url):
    response = requests.get(url.format(url = originalURL))
    return response.json()

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
    

