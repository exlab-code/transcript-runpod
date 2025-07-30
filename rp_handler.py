#!/usr/bin/env python3
"""
RunPod Serverless GPU Transcription Handler
Clean version with minimal dependencies for faster build
"""

import runpod
from faster_whisper import WhisperModel
import tempfile
import base64
import os
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance (loaded once per worker)
whisper_model = None

def clean_hallucinated_text(text: str) -> str:
    """Clean hallucinated and repetitive text from Whisper output"""
    if not text or len(text.strip()) < 3:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Detect repetitive patterns
    words = text.split()
    if len(words) < 4:
        return text
    
    # Check for excessive repetition of phrases
    for phrase_len in [2, 3, 4, 5]:
        if len(words) >= phrase_len * 3:
            for i in range(len(words) - phrase_len * 3 + 1):
                phrase = words[i:i + phrase_len]
                
                # Count consecutive repetitions
                repetitions = 1
                pos = i + phrase_len
                
                while pos + phrase_len <= len(words):
                    if words[pos:pos + phrase_len] == phrase:
                        repetitions += 1
                        pos += phrase_len
                    else:
                        break
                
                # If we find 3+ repetitions, truncate
                if repetitions >= 3:
                    words = words[:i + phrase_len * 2]
                    break
    
    return ' '.join(words)

def load_whisper_model():
    """Initialize the Whisper model (called once per worker)"""
    global whisper_model
    
    if whisper_model is None:
        try:
            model_size = os.getenv("WHISPER_MODEL", "medium")
            compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
            
            logger.info(f"Loading faster-whisper model: {model_size} with {compute_type} precision on GPU")
            whisper_model = WhisperModel(
                model_size, 
                device="cuda",
                compute_type=compute_type,
                cpu_threads=1,
                local_files_only=False
            )
            logger.info("✅ Faster-whisper GPU model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load whisper model: {e}")
            raise e
    
    return whisper_model

def handler(job):
    """Handle transcription requests from RunPod serverless"""
    processing_start_time = datetime.now()
    
    try:
        # Load model if not already loaded
        model = load_whisper_model()
        
        # Extract job inputs
        input_data = job['input']
        audio_b64 = input_data['audio_b64']
        session_id = input_data.get('session_id', 'unknown')
        chunk_index = input_data.get('chunk_index', 0)
        
        logger.info(f"🎙️ Processing [{session_id}:{chunk_index}] via GPU serverless")
        
        # Decode base64 audio data
        try:
            audio_data = base64.b64decode(audio_b64)
        except Exception as e:
            return {"success": False, "error": f"Invalid base64 audio data: {str(e)}"}
        
        logger.info(f"📦 Decoded audio: {len(audio_data)} bytes")
        
        # Create temporary file for transcription
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Transcription with anti-hallucination settings
            transcription_start = datetime.now()
            
            language = os.getenv("WHISPER_LANGUAGE", "de")
            beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "3"))
            temperature = float(os.getenv("WHISPER_TEMPERATURE", "0.2"))
            
            segments, info = model.transcribe(
                temp_path,
                language=language,
                beam_size=beam_size,
                temperature=temperature,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=100,
                    min_speech_duration_ms=100,
                    speech_pad_ms=100
                ),
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4
            )
            
            # Convert segments to list
            segments_list = list(segments)
            transcription_time = (datetime.now() - transcription_start).total_seconds()
            
            # Format response with hallucination cleaning
            cleaned_segments = []
            full_text_parts = []
            
            for segment in segments_list:
                # Clean the segment text
                original_text = segment.text.strip()
                cleaned_text = clean_hallucinated_text(original_text)
                
                # Skip empty segments after cleaning
                if not cleaned_text:
                    continue
                
                cleaned_segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": cleaned_text,
                    "speaker": "SPEAKER_00",
                    "confidence": float(getattr(segment, 'avg_logprob', 0.0))
                })
                
                full_text_parts.append(cleaned_text)
            
            # Join cleaned text
            full_text = " ".join(full_text_parts)
            
            # Calculate processing metrics
            total_processing_time = (datetime.now() - processing_start_time).total_seconds()
            audio_duration = info.duration
            rtf = total_processing_time / audio_duration if audio_duration > 0 else 0
            
            # Response format compatible with existing Railway app
            result = {
                "text": full_text,
                "language": info.language,
                "language_probability": float(info.language_probability),
                "duration": float(audio_duration),
                "segments": cleaned_segments,
                "processing_info": {
                    "transcription_time": transcription_time,
                    "total_processing_time": total_processing_time,
                    "real_time_factor": rtf,
                    "model": os.getenv("WHISPER_MODEL", "medium"),
                    "compute_type": os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
                    "device": "cuda",
                    "speakers_detected": len(set(seg["speaker"] for seg in cleaned_segments)),
                    "segments_count": len(cleaned_segments),
                    "serverless": True
                }
            }
            
            # Clean log output
            logger.info(f"✅ [{session_id}:{chunk_index}] GPU RTF: {rtf:.2f} | {len(cleaned_segments)} segments")
            
            return result
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ Transcription failed for [{session_id}:{chunk_index}]: {e}")
        return {
            "error": str(e),
            "session_id": session_id,
            "chunk_index": chunk_index
        }

# RunPod serverless entry point
runpod.serverless.start({"handler": handler})