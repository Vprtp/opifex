import requests
from random import choice
from bs4 import BeautifulSoup
import os
import urllib.request
import urllib.parse
from basemodule import BaseModule, ModuleResultType
import config

#list of possible user agent headers to choose from
userAgents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
              "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
              "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
              "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Edge/79.0.1451.30 Safari/537.36"]

def formatURLFriendly(text, use_plus_for_spaces=True):
    """
    Format text to be URL-friendly.
    
    Args:
        text (str): The text to encode
        use_plus_for_spaces (bool): 
            - True: Replace spaces with '+' (commonly used in query strings)
            - False: Replace spaces with '%20' (standard URL encoding)
    
    Returns:
        str: URL-encoded text
    """
    if use_plus_for_spaces:
        return urllib.parse.quote_plus(text, safe='')
    else:
        return urllib.parse.quote(text, safe='')

def getRandomHeaders() -> dict[str]:
    return {'User-Agent': choice(userAgents)}

def getImageURLs(pageURL:str) -> list[str]:
    response = requests.get(pageURL, headers=getRandomHeaders())
    soup = BeautifulSoup(response.text, 'html.parser')
    images:list[str] = []
    imgs = soup.find_all("img")
    for img in imgs:
        images.append(img['src'])
    return images

#this could also be made with requests.get, but right now this approach is easier
def downloadImage(url, save_dir, filename=None):
    """
    Download an image using urllib (no external dependencies).
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if filename is None:
        filename = url.split('/')[-1].split('?')[0]
        if '.' not in filename:
            filename = 'downloaded_image.jpg'
    
    save_path = os.path.join(save_dir, filename)
    
    # Download the image
    urllib.request.urlretrieve(url, save_path)
    
    return save_path

def saveImages(sourceURLs:list[str], destinationDir:str) -> None:
    for source in sourceURLs:
        try:
            downloadImage(source,destinationDir)
        except:
            print(f"Failed to download image {source}.")

def findPictures(searchTerms:str, endDir:str, providerURL:str):
    """
    "providerURL" must be in a form along the lines of "https://my.providers.website/images?q={terms}", 
    where "{terms}" MUST be written exactly like this
    """
    searchTerms = formatURLFriendly(searchTerms)
    if "{terms}" not in providerURL:
        raise KeyError("Please add the {terms} variable in your providerURL.")
    else:
        imgs:list[str] = getImageURLs(providerURL.format(terms=searchTerms))
        saveImages(imgs, endDir)

class ImageFinder(BaseModule):
    def __init__(self):
        self.name = "ImageFinder"
        self.description = "Module that finds and downloads online images onto a given directory.\n\nParameters:\n-search: Search terms for the requested images\n-destDir: Directory where images will be downloaded to"
        self.requiredArgs = [("search",str), ("destDir",str)]
        self.returnedDataTypes = []
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            findPictures(kwargs["search"], kwargs["destDir"], config.imageSearchProvider)
            return ModuleResultType(None,{})
        except Exception as e:
            return ModuleResultType(e,{})