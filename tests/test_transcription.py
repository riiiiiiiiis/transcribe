import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock


def test_youtube_audio_download():
    """Test downloading audio from YouTube"""
    from app.transcription import download_audio_from_youtube
    
    # Test with a real YouTube URL (short video for testing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Mock the yt-dlp download to avoid actual download during tests
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        # Create a temporary file to simulate downloaded audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 180,
            'requested_downloads': [{'filepath': tmp_path}]
        }
        
        result = download_audio_from_youtube(test_url)
        
        assert result is not None
        assert 'audio_path' in result
        assert 'title' in result
        assert 'duration' in result
        assert result['title'] == 'Test Video'
        assert result['duration'] == 180
        
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_openai_whisper_integration():
    """Test integration with OpenAI Whisper"""
    from app.transcription import transcribe_with_openai
    
    # Create a mock audio file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write(b'mock audio data')
    
    # Mock OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock transcription response
        mock_response = MagicMock()
        mock_response.text = "This is a test transcription"
        mock_response.segments = [
            {"start": 0.0, "end": 5.0, "text": "This is a test"},
            {"start": 5.0, "end": 10.0, "text": " transcription"}
        ]
        
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        result = transcribe_with_openai(tmp_path)
        
        assert result is not None
        assert 'content' in result
        assert 'timestamps' in result
        assert result['content'] == "This is a test transcription"
        assert len(result['timestamps']) == 2
        assert result['timestamps'][0]['text'] == "This is a test"
        
        # Verify OpenAI was called correctly
        mock_client.audio.transcriptions.create.assert_called_once()
        
        # Cleanup
        os.remove(tmp_path)


def test_full_transcription_pipeline():
    """Test full process of transcription"""
    from app.transcription import process_video_transcription
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Mock all external dependencies
    with patch('app.transcription.download_audio_from_youtube') as mock_download, \
         patch('app.transcription.transcribe_with_openai') as mock_transcribe, \
         patch('app.transcription.save_transcript_to_db') as mock_save:
        
        # Mock download response
        mock_download.return_value = {
            'audio_path': '/tmp/test_audio.mp3',
            'title': 'Test Video',
            'duration': 180
        }
        
        # Mock transcription response
        mock_transcribe.return_value = {
            'content': 'This is the full transcription',
            'timestamps': [
                {"start": 0.0, "end": 10.0, "text": "This is the full transcription"}
            ]
        }
        
        # Mock database save
        import uuid
        transcript_id = str(uuid.uuid4())
        mock_save.return_value = transcript_id
        
        # Mock database session
        mock_db = MagicMock()
        
        # Execute the pipeline
        result = process_video_transcription(test_url, mock_db)
        
        # Verify the result
        assert result is not None
        assert 'transcript_id' in result
        assert 'title' in result
        assert 'duration' in result
        assert 'content' in result
        assert 'timestamps' in result
        assert 'created_at' in result
        
        assert result['title'] == 'Test Video'
        assert result['duration'] == 180
        assert result['content'] == 'This is the full transcription'
        
        # Verify all functions were called
        mock_download.assert_called_once_with(test_url)
        mock_transcribe.assert_called_once_with('/tmp/test_audio.mp3')
        mock_save.assert_called_once()