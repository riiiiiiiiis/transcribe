import os
import tempfile
import logging
from datetime import datetime
import yt_dlp
import openai
from sqlalchemy.orm import Session

from .config import OPENAI_API_KEY
from .models import Transcript
from .schemas import TranscriptResponse

logger = logging.getLogger(__name__)

# Initialize OpenAI client (will be created when needed)
def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return openai.OpenAI(api_key=OPENAI_API_KEY)


def process_video_transcription(youtube_url: str, db: Session) -> dict:
    """
    Main flow for processing video transcription:
    1. Download audio from YouTube (yt-dlp)
    2. Send to OpenAI Whisper API
    3. Save result to DB
    4. Clean up temporary files
    5. Return ready transcript
    """
    audio_path = None
    
    try:
        # Step 1: Download audio from YouTube
        logger.info(f"Starting audio download for URL: {youtube_url}")
        download_result = download_audio_from_youtube(youtube_url)
        audio_path = download_result['audio_path']
        title = download_result['title']
        duration = download_result['duration']
        
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        logger.info(f"Audio downloaded: {file_size} bytes")
        
        # Step 2: Transcribe with OpenAI Whisper
        logger.info("Starting transcription with OpenAI Whisper")
        transcription_result = transcribe_with_openai(audio_path)
        content = transcription_result['content']
        timestamps = transcription_result['timestamps']
        
        # Step 3: Save to database
        logger.info("Saving transcript to database")
        transcript_id = save_transcript_to_db(
            db=db,
            youtube_url=youtube_url,
            title=title,
            duration=duration,
            content=content,
            timestamps=timestamps
        )
        
        logger.info(f"Transcription completed: {transcript_id}")
        
        # Return ready transcript
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        return {
            "transcript_id": transcript.id,
            "title": transcript.title,
            "duration": transcript.duration,
            "content": transcript.content,
            "timestamps": transcript.timestamps,
            "created_at": transcript.created_at
        }
        
    finally:
        # Step 4: Clean up temporary files
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info("Temporary audio file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")


def download_audio_from_youtube(url: str) -> dict:
    """Download audio from YouTube, return path to file"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'cookiefile': None,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Get the actual downloaded file path
        audio_path = None
        if 'requested_downloads' in info and info['requested_downloads']:
            audio_path = info['requested_downloads'][0]['filepath']
        else:
            # Fallback: search for the file
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    audio_path = os.path.join(temp_dir, file)
                    break
        
        if not audio_path or not os.path.exists(audio_path):
            raise Exception("Failed to download audio file")
        
        return {
            'audio_path': audio_path,
            'title': info.get('title', 'Unknown Title'),
            'duration': info.get('duration', 0)
        }


def transcribe_with_openai(audio_file_path: str) -> dict:
    """Send audio to OpenAI Whisper, return transcript with timestamps"""
    client = get_openai_client()
    
    with open(audio_file_path, 'rb') as audio_file:
        # Request transcription with timestamps
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    # Extract content and timestamps
    content = response.text
    timestamps = []
    
    if hasattr(response, 'segments') and response.segments:
        for segment in response.segments:
            timestamps.append({
                "start": getattr(segment, 'start', 0.0),
                "end": getattr(segment, 'end', 0.0),
                "text": getattr(segment, 'text', '')
            })
    
    return {
        'content': content,
        'timestamps': timestamps
    }


def save_transcript_to_db(db: Session, youtube_url: str, title: str, 
                         duration: float, content: str, timestamps: list) -> str:
    """Save transcript to database, return transcript ID"""
    transcript = Transcript(
        youtube_url=youtube_url,
        title=title,
        duration=duration,
        content=content,
        timestamps=timestamps
    )
    
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    return str(transcript.id)