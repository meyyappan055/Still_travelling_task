from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(id):

    has_transcript = False
    try : 
        content = YouTubeTranscriptApi.get_transcript(id)
        text = ""
        for each in content:
            text+=each["text"] + " "

        has_transcript = True
        return text.strip() , has_transcript
    except:
        return "no transcripts found", has_transcript

