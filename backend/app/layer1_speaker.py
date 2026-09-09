"""
Layer 1 — Speaker Verification - Surya
Uses speechbrain/spkrec-ecapa-voxceleb for 192-dim embeddings
"""

import io
import torch
import soundfile as sf
import numpy as np
from scipy import signal
from speechbrain.inference.speaker import EncoderClassifier
from speechbrain.utils.fetching import LocalStrategy

# Load model once at module import (not per-request)
# local_strategy=COPY avoids symlinking into savedir, which fails on Windows
# without admin rights or Developer Mode enabled.
MODEL = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
    run_opts={"device": "cpu"},  # Use CPU for demo; change to "cuda" if GPU available
    local_strategy=LocalStrategy.COPY
)


def _load_audio(audio_bytes: bytes) -> torch.Tensor:
    """
    Load audio bytes and convert to 16kHz mono waveform.
    Includes fallback decoding for browser audio formats.
    """
    try:
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
    except Exception:
        import librosa
        audio_data, sample_rate = librosa.load(io.BytesIO(audio_bytes), sr=16000)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Resample to 16kHz if needed
    if sample_rate != 16000:
        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = signal.resample(audio_data, num_samples)

    # Convert to tensor with shape (1, num_samples)
    waveform = torch.tensor(audio_data, dtype=torch.float32).unsqueeze(0)

    return waveform


def _cosine_similarity(embedding1: torch.Tensor, embedding2: torch.Tensor) -> float:
    """
    Compute cosine similarity between two embeddings.

    Returns:
        Similarity score normalized to 0-1 range
    """
    # Ensure 1D tensors
    e1 = embedding1.flatten()
    e2 = embedding2.flatten()

    # Cosine similarity: ranges from -1 to 1
    cos_sim = torch.nn.functional.cosine_similarity(
        e1.unsqueeze(0),
        e2.unsqueeze(0)
    ).item()

    # Normalize to 0-1 range: (cos_sim + 1) / 2
    # -1 -> 0, 0 -> 0.5, 1 -> 1
    normalized_score = (cos_sim + 1) / 2

    return normalized_score


def enroll_speaker(audio_bytes: bytes) -> dict:
    """
    Extract speaker embedding from enrollment audio.

    Args:
        audio_bytes: WAV audio (16kHz, mono, min 3s)

    Returns:
        {"embedding": list[float]}  # 192-dim
    """
    waveform = _load_audio(audio_bytes)

    # Extract embedding using ECAPA-TDNN
    # encode_batch expects (batch, time) tensor
    embedding = MODEL.encode_batch(waveform)

    # Squeeze to 1D: (1, 1, 192) -> (192,)
    embedding = embedding.squeeze()

    return {"embedding": embedding.tolist()}


def verify_speaker(audio_bytes: bytes, stored_embedding: list[float]) -> dict:
    """
    Compare audio against stored voiceprint.

    Args:
        audio_bytes: WAV audio (16kHz, mono, min 2s)
        stored_embedding: Previously enrolled 192-dim embedding

    Returns:
        {"score": float, "embedding": list[float]}
        score: cosine similarity 0-1 (higher = more similar)
    """
    waveform = _load_audio(audio_bytes)

    # Extract embedding from new audio
    new_embedding = MODEL.encode_batch(waveform).squeeze()

    # Convert stored embedding to tensor
    stored_tensor = torch.tensor(stored_embedding)

    # Compute similarity score
    score = _cosine_similarity(new_embedding, stored_tensor)

    return {
        "score": float(score),
        "embedding": new_embedding.tolist()
    }
