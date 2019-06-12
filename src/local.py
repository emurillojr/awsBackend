import json
import boto3
import re
import codecs
from audioUtils import *
from moviepy.editor import *
from moviepy import editor
from moviepy.video.tools.subtitles import SubtitlesClip
from time import gmtime, strftime
from srtUtils import *
from videoUtils import *


def main():
   transcript = open("15006.json","r").read()
   sourceLangCode = "EN"
   srtFileName = "outputTEST.SRT"
   originalClipName = "15006_FFOS_Regional_Sales_Videos_Heather_Gilker_1920x1080.mp4"
   subtitlesFileName = "outputTEST.SRT"
   outputFileName = "newVid123.mp4"
   writeTranscriptToSRT(transcript, sourceLangCode, srtFileName)
   createVideo( originalClipName, subtitlesFileName, outputFileName, useOriginalAudio=True )

main()
