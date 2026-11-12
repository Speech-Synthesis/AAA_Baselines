"""
AAA-ASR Transcriber — Local Whisper ASR Wrapper

This module handles audio transcription using local Whisper models.
It is deliberately separated from the phrase verification logic.

Key design decisions:
- Uses local Whisper model only (no hosted API calls, no OpenAI API key)
- Model files staged locally for offline runtime
- Device selection: CUDA if available, else CPU
- Thread-safe lazy model loading
"""

import io
import os
import sys
from typing import Optional
from dataclasses import dataclass

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


@dataclass
class ASRResult:
    """Result from ASR transcription.
    
    Attributes:
        text: Transcribed text
        confidence: Average log probability (proxy for confidence)
        no_speech_prob: Probability that the segment contains no speech
        language: Detected language
        duration: Audio duration in seconds
    """
    text: str
    confidence: float = 0.0
    no_speech_prob: float = 0.0
    language: str = "en"
    duration: float = 0.0


class Transcriber:
    """
    Local Whisper ASR transcriber.
    
    This class wraps the local Whisper model for transcription.
    It does NOT make phrase verification decisions — that is the
    responsibility of PhraseVerifier.
    
    Usage:
        transcriber = Transcriber(model_size="base")
        result = transcriber.transcribe(audio_bytes)
        print(result.text)
    """
    
    def __init__(
        self,
        model_size: str = None,
        model_dir: str = None,
        device: str = "auto",
    ):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large).
                        Defaults to WHISPER_MODEL env var or "base".
            model_dir: Directory to store/load model files.
                       Defaults to WHISPER_MODEL_DIR env var or E: drive path.
            device: Device to use ("auto", "cpu", "cuda").
        """
        self.model_size = model_size or os.getenv("WHISPER_MODEL", "base")
        self.model_dir = model_dir or os.getenv(
            "WHISPER_MODEL_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "..", ".models", "whisper")
        )
        self.device = device
        self._model = None
    
    def _get_model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            import torch
            import whisper
            
            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            print(f"[AAA-ASR] Loading Whisper model: {self.model_size} on {device}")
            
            # Ensure model directory exists
            os.makedirs(self.model_dir, exist_ok=True)
            
            self._model = whisper.load_model(
                self.model_size,
                device=device,
                download_root=self.model_dir,
            )
            print(f"[AAA-ASR] Whisper model loaded successfully")
        return self._model
    
    def transcribe(self, audio_bytes: bytes) -> ASRResult:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Raw audio bytes (WAV format, 16kHz mono expected)
            
        Returns:
            ASRResult with transcription and confidence information
        """
        import torch
        import numpy as np
        import soundfile as sf
        
        model = self._get_model()
        
        # Load audio from bytes
        audio_io = io.BytesIO(audio_bytes)
        audio_data, sample_rate = sf.read(audio_io)
        
        # Calculate duration
        duration = len(audio_data) / sample_rate
        
        # Convert to float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Stereo to mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            from scipy import signal
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)
            duration = len(audio_data) / 16000
        
        # Transcribe
        result = model.transcribe(
            audio_data,
            language="en",
            fp16=torch.cuda.is_available(),
        )
        
        text = result.get("text", "").strip()
        
        # Extract confidence from segments
        segments = result.get("segments", [])
        avg_logprob = 0.0
        no_speech_prob = 0.0
        if segments:
            avg_logprob = sum(s.get("avg_logprob", 0) for s in segments) / len(segments)
            no_speech_prob = sum(s.get("no_speech_prob", 0) for s in segments) / len(segments)
        
        # Convert log probability to a 0-1 confidence score
        # avg_logprob is typically between -1 (low conf) and 0 (high conf)
        import math
        confidence = math.exp(avg_logprob) if avg_logprob else 0.0
        confidence = max(0.0, min(1.0, confidence))
        
        return ASRResult(
            text=text,
            confidence=confidence,
            no_speech_prob=no_speech_prob,
            language=result.get("language", "en"),
            duration=duration,
        )
