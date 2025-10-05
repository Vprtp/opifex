import time
import pathlib
import reddit
import tts
import alignSRT
import video
import os

# WARNING: THIS PROGRAM CURRENTLY ONLY WORKS ON LINUX
p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")

generatedVideoFolder:str = p+"generated/video/"
accountName:str = "@reddit_stories"

#TEST RUN:
initTime = time.time()
a = reddit.getJSON("https://www.reddit.com/r/AskReddit/comments/15np0f/is_there_anybody_here_who_truly_believes_they/")
comments = reddit.getComments(a)
title = reddit.getTitle(a)
print(f"Title: '{title}' Upvotes: {reddit.getUpvotes(a)}")
for i in range(len(comments)):
    print(f"COMMENT {i}:\n{comments[i]}")
    loc:tuple[str,str] = tts.generate(reddit.getTitle(a),comments[i])
    print(f"Saved files in {loc[0]} and {loc[1]}")
    parentDir:str = str(pathlib.Path(loc[1]).parents[0])
    sub:str = alignSRT.generateSubtitles(loc[1],tts.cleanText(comments[i]),parentDir)[1]
    print(f"Saved subtitles in {sub}")
    video.computeVideo(generatedVideoFolder+pathlib.Path(parentDir).name+".mp4",title,sub,loc[0],loc[1],name=accountName)
print(f"\n\nTask completed successfully in {time.time()-initTime} seconds.\nAverage time per comment: {(time.time()-initTime)/len(comments)}")

