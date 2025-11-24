import requests
from basemodule import BaseModule, ModuleResultType

def getUrl(original:str,removeParamters:bool=True):
    response = requests.get(original, allow_redirects=True)
    if removeParamters:
        response = response.url.split("?")[0]
    else:
        response = response.url
    return response

class URLunshortener(BaseModule):
    def __init__(self):
        self.name = "URLunshortener"
        self.description = "Module that returns the final URL from redirections by a given one (thus 'unshortening' shortened URLs)\n\nParameters:\n-url: URL that needs to be unshortened\n-rmpars: Whether or not to remove parameters from the returned URL"
        self.requiredArgs = [("url",str),("rmpars",bool)]
        self.returnedDataTypes = [("url",str)]
        self.dependencies = []
    
    def execute(self, **kwargs):
        try:
            url:str = getUrl(kwargs["url"],kwargs["rmpars"])
            return ModuleResultType(None,{"url":url})
        except Exception as e:
            return ModuleResultType(e,{})

