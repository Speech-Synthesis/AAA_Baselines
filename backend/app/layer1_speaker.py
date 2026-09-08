"""
Layer 1 — Speaker Verification - Surya
Uses speechbrain/spkrec-ecapa-voxceleb for 192-dim embeddings
"""

import io
import numpy as np

# Phase 1: Stub implementation with mocked returns
# Phase 2: Uncomment real model loading below

# from speechbrain.inference.speaker import SpeakerRecognition
# MODEL = SpeakerRecognition.from_hparams(
#     source="speechbrain/spkrec-ecapa-voxceleb",
#     savedir="pretrained_models/spkrec-ecapa-voxceleb"
# )


def enroll_speaker(audio_bytes: bytes) -> dict:
    """
    Extract speaker embedding from enrollment audio.

    Args:
        audio_bytes: WAV audio (16kHz, mono, min 3s)

    Returns:
        {"embedding": list[float]}  # 192-dim
    """
    # === STUB (Phase 1) ===
    # Return random 192-dim embedding for testing
    embedding = np.random.randn(192).tolist()
    return {"embedding": embedding}

    # === REAL (Phase 2) ===
    # import torchaudio
    # waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
    # if sample_rate != 16000:
    #     resampler = torchaudio.transforms.Resample(sample_rate, 16000)
    #     waveform = resampler(waveform)
    # embedding = MODEL.encode_batch(waveform).squeeze().tolist()
    # return {"embedding": embedding}


def verify_speaker(audio_bytes: bytes, stored_embedding: list[float]) -> dict:
    """
    Compare audio against stored voiceprint.

    Args:
        audio_bytes: WAV audio (16kHz, mono, min 2s)
        stored_embedding: Previously enrolled 192-dim embedding

    Returns:
        {"score": float, "embedding": list[float]}
        score: cosine similarity 0-1
    """
    # === STUB (Phase 1) ===
    # Return random score and embedding for testing
    new_embedding = np.random.randn(192).tolist()
    score = np.random.uniform(0.5, 1.0)  # Simulate mostly positive matches
    return {"score": float(score), "embedding": new_embedding}

    # === REAL (Phase 2) ===
    # import torchaudio
    # import torch
    # waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
    # if sample_rate != 16000:
    #     resampler = torchaudio.transforms.Resample(sample_rate, 16000)
    #     waveform = resampler(waveform)
    # new_embedding = MODEL.encode_batch(waveform).squeeze()
    #
    # # Cosine similarity
    # stored = torch.tensor(stored_embedding)
    # score = torch.nn.functional.cosine_similarity(
    #     new_embedding.unsqueeze(0),
    #     stored.unsqueeze(0)
    # ).item()
    # score = (score + 1) / 2  # Normalize to 0-1
    #
    # return {"score": float(score), "embedding": new_embedding.tolist()}
