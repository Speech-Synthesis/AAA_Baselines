"""
Layer 2 — Deepfake Detection - Nandan
Uses Wav2Vec2 fine-tuned for deepfake/spoof detection
Labels: {0: 'real', 1: 'fake'}
Note: Modern high-quality TTS (ElevenLabs, etc.) may evade detection
"""

import io
import os
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from scipy import signal
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

# Model paths - local model takes priority over HuggingFace
_MODEL = None
_FEATURE_EXTRACTOR = None

# Local model path (relative to backend/)
_LOCAL_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "ad"
# Fallback to HuggingFace if local not available
_HF_MODEL_NAME = "garystafford/wav2vec2-deepfake-voice-detector"


def _get_model_path() -> str:
    """Get model path - local if exists, else HuggingFace."""
    if _LOCAL_MODEL_PATH.exists() and (_LOCAL_MODEL_PATH / "config.json").exists():
        return str(_LOCAL_MODEL_PATH)
    return _HF_MODEL_NAME


def _load_model():
    """Lazy load the deepfake detection model."""
    global _MODEL, _FEATURE_EXTRACTOR

    if _MODEL is not None:
        return

    model_path = _get_model_path()
    is_local = model_path.startswith(str(_LOCAL_MODEL_PATH.parent))
    source = "local" if is_local else "HuggingFace"

    print(f"Loading AD model from {source}: {model_path}")
    _MODEL = AutoModelForAudioClassification.from_pretrained(model_path, local_files_only=is_local)
    _FEATURE_EXTRACTOR = AutoFeatureExtractor.from_pretrained(model_path, local_files_only=is_local)
    _MODEL.eval()
    print(f"Successfully loaded AD model")
    print(f"Labels: {_MODEL.config.id2label}")

    if torch.cuda.is_available():
        _MODEL = _MODEL.to("cuda")
        print("AD model moved to CUDA")


def _load_audio(audio_bytes: bytes) -> np.ndarray:
    """Load audio bytes and convert to 16kHz mono waveform."""
    audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Resample to 16kHz if needed
    if sample_rate != 16000:
        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = signal.resample(audio_data, num_samples)

    return audio_data.astype(np.float32)


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
        waveform = _load_audio(audio_bytes)

        inputs = _FEATURE_EXTRACTOR(
            waveform, sampling_rate=16000, return_tensors="pt", padding=True
        )

        device = next(_MODEL.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = _MODEL(**inputs).logits
            probs = torch.softmax(logits, dim=-1)

            # Model labels: {0: 'real', 1: 'fake'}
            real_prob = probs[0, 0].item()
            fake_prob = probs[0, 1].item()

        # Map to our API format: bonafide/spoof
        if real_prob > fake_prob:
            label = "bonafide"
            confidence = real_prob
        else:
            label = "spoof"
            confidence = fake_prob

        return {"label": label, "confidence": float(confidence)}

    except Exception as e:
        print(f"Error in detect_spoof: {e}")
        raise
