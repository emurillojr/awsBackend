# ==================================================================================
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ==================================================================================
#
# transcribeUtils.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
#
# Purpose: The program provides a number of utility functions for leveraging the Amazon Transcribe API
#
# Change Log:
#          6/29/2018: Initial version
#
# ==================================================================================

import boto3
import uuid
import requests
import time
import json
import re
import codecs
from audioUtils import *
from moviepy.editor import *
from moviepy import editor
from moviepy.video.tools.subtitles import SubtitlesClip
from time import gmtime, strftime
from srtUtils import *
from videoUtils import *

# ==================================================================================
# Function: createTranscribeJob
# Purpose: Function to format the input parameters and invoke the Amazon Transcribe service
# Parameters:
#                 region - the AWS region in which to run AWS services (e.g. "us-east-1")
#                 bucket - the Amazon S3 bucket name (e.g. "mybucket/") found in region that contains the media file for processing.
#                 mediaFile - the content to process (e.g. "myvideo.mp4")
#
# ==================================================================================
def createTranscribeJob( region, bucket, mediaFile ):

	# Set up the Transcribe client
	transcribe = boto3.client('transcribe', aws_access_key_id='AKIATYPOP5Z73TZQSJHB', aws_secret_access_key='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')
	

	# Set up the full uri for the bucket and media file

	mediaUri = "https://fiamhackathon2019.s3.amazonaws.com/15006_FFOS_Regional_Sales_Videos_Heather_Gilker_1920x1080.mp4"
	jobName = "transcribe_" + uuid.uuid4().hex
	print( "Creating Job: " + jobName )

	# Use the uuid functionality to generate a unique job name.  Otherwise, the Transcribe service will return an error
	response = transcribe.start_transcription_job( TranscriptionJobName=jobName , \
		LanguageCode = "en-US", \
		MediaFormat = "mp4", \
		Media = { "MediaFileUri" : mediaUri },\
		)

	#print( "\n==> Transcription Job: " + response["TranscriptionJob"]["TranscriptionJobName"] + "\n\tIn Progress")
	# return the response structure found in the Transcribe Documentation
	return response


# ==================================================================================
# Function: getTranscriptionJobStatus
# Purpose: Helper function to return the status of a job running the Amazon Transcribe service
# Parameters:
#                 jobName - the unique jobName used to start the Amazon Transcribe job
# ==================================================================================
def getTranscriptionJobStatus( jobName ):
	transcribe = boto3.client('transcribe', aws_access_key_id='AKIATYPOP5Z73TZQSJHB', aws_secret_access_key='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')

	response = transcribe.get_transcription_job( TranscriptionJobName=jobName )
	return response


# ==================================================================================
# Function: getTranscript
# Purpose: Helper function to return the transcript based on the signed URI in S3 as produced by the Transcript job
# Parameters:
#                 transcriptURI - the signed S3 URI for the Transcribe output
# ==================================================================================
def getTranscript( transcriptURI ):
	# Get the resulting Transcription Job and store the JSON response in transcript
	result = requests.get( transcriptURI )

	return result.text


def main():

   localtime = time.localtime(time.time())
   print(localtime)

   region = "us-east-1"
   bucket = "fiamhackathon2019"
   mediaFile = "15006_FFOS_Regional_Sales_Videos_Heather_Gilker_1920x1080.mp4"
   s3 = boto3.resource('s3', aws_access_key_id='AKIATYPOP5Z73TZQSJHB', aws_secret_access_key='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')

   transcoder = boto3.client('elastictranscoder', aws_access_key_id='AKIATYPOP5Z73TZQSJHB', aws_secret_access_key='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')
   
   response = createTranscribeJob( region, bucket, mediaFile )
   
   print( "\n==> Transcription Job: " + response["TranscriptionJob"]["TranscriptionJobName"] + "\n\tIn Progress"),

   while( response["TranscriptionJob"]["TranscriptionJobStatus"] == "IN_PROGRESS"):
   		print( "."),
		time.sleep( 30 )
		response = getTranscriptionJobStatus( response["TranscriptionJob"]["TranscriptionJobName"] )

   print( "\nJob Complete")
   print( "\tStart Time: " + str(response["TranscriptionJob"]["CreationTime"]) )
   print( "\tEnd Time: "  + str(response["TranscriptionJob"]["CompletionTime"]) )
   print( "\tTranscript URI: " + str(response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]) )

   transcript = getTranscript( str(response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]) ) 
   print ("\n Transcript")
   print (transcript)

   sourceLangCode = "EN"
   srtFileName = uuid.uuid4().hex +"outputTEST.SRT"
   writeTranscriptToSRT(transcript, sourceLangCode, srtFileName)
   s3.meta.client.upload_file(srtFileName, bucket, srtFileName)
   
   outputFileName =  uuid.uuid4().hex + "newVid.mp4"
   createVideo( mediaFile, srtFileName, outputFileName, useOriginalAudio=True )
   s3.meta.client.upload_file(outputFileName, bucket, outputFileName)
	
   pipelineId = 1
   paginator = transcoder.get_paginator('list_pipelines')
   for page in paginator.paginate():
	   for pipeline in page['Pipelines']:
		   pipelineId = pipeline['Id']
   print(pipelineId)

   transcoder.create_job(PipelineId=pipelineId,
    Input={
        'Key':outputFileName,
        'FrameRate': 'auto',
        'Resolution': 'auto',
        'AspectRatio': 'auto',
        'Interlaced': 'auto',
        'Container': 'mp4'         
    },   
    Output={
        'Key': 'OutputApi',
        'ThumbnailPattern': '',       
        'Rotate': '0',
        'PresetId': '1560275750241-pnt4t7'                
    },   
    OutputKeyPrefix='Web/') 

   localtime = time.localtime(time.time())
   print(localtime)

main()