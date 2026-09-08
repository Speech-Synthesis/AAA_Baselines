"""
Layer 2 — Deepfake Detection - Nandan
Uses HyperMoon/wav2vec2-base-960h-finetuned-deepfake for spoof detection
Phase 1: Pretrained baseline (no training)
"""

import io
import torch
import soundfile as sf
import numpy as np
from scipy import signal
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
from typing import Optional

# Load model at module import time
# Primary model: HyperMoon/wav2vec2-base-960h-finetuned-deepfake
# Fallback: abhishtagatya/wav2vec2-base-960h-asv19-deepfake
_MODEL = None
_FEATURE_EXTRACTOR = None
_MODEL_NAME = None

def _load_model():
    """Lazy load the deepfake detection model."""
    global _MODEL, _FEATURE_EXTRACTOR, _MODEL_NAME
    
    if _MODEL is not None:
        return
    
    primary_model = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
    fallback_model = "abhishtagatya/wav2vec2-base-960h-asv19-deepfake"
    
    try:
        print(f"Loading model: {primary_model}")
        _MODEL = Wav2Vec2ForSequenceClassification.from_pretrained(primary_model)
        _FEATURE_EXTRACTOR = Wav2Vec2FeatureExtractor.from_pretrained(primary_model)
        _MODEL_NAME = primary_model
        print(f"Successfully loaded: {primary_model}")
    except Exception as e:
        print(f"Failed to load {primary_model}: {e}")
        print(f"Attempting fallback: {fallback_model}")
        try:
            _MODEL = Wav2Vec2ForSequenceClassification.from_pretrained(fallback_model)
            _FEATURE_EXTRACTOR = Wav2Vec2FeatureExtractor.from_pretrained(fallback_model)
            _MODEL_NAME = fallback_model
            print(f"Successfully loaded fallback: {fallback_model}")
        except Exception as e2:
            print(f"Failed to load fallback model: {e2}")
            raise RuntimeError(f"Could not load either model: {e}, {e2}")
    
    _MODEL.eval()
    # Move to GPU if available
    if torch.cuda.is_available():
        _MODEL = _MODEL.to("cuda")


def detect_spoof(audio_bytes: bytes) -> dict:
    """
    Detect if audio is bonafide (real) or spoof (deepfake/replay/TTS).

    Args:
        audio_bytes: WAV audio (16kHz, mono)

    Returns:
        {"label": "bonafide" | "spoof", "confidence": float}
    """
    _load_model()
    
    try:
        # Load audio from bytes (soundfile avoids torchaudio's torchcodec/FFmpeg
        # dependency, which isn't available on this machine)
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Resample if necessary
        if sample_rate != 16000:
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)

        # Extract features
        inputs = _FEATURE_EXTRACTOR(
            audio_data,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        
        # Move inputs to same device as model
        device = next(_MODEL.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            logits = _MODEL(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
            predicted_class = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, predicted_class].item()
        
        # Class mapping: 0=bonafide, 1=spoof (standard for ASVspoof models)
        label = "bonafide" if predicted_class == 0 else "spoof"
        
        return {
            "label": label,
            "confidence": float(confidence)
        }
    
    except Exception as e:
        print(f"Error in detect_spoof: {e}")
        raise
