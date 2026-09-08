"""
Layer 2 — Deepfake Detection - Nandan
Uses HyperMoon/wav2vec2-base-960h-finetuned-deepfake for spoof detection
"""

import io
import random

# Phase 1: Stub implementation with mocked returns
# Phase 2: Uncomment real model loading below

# from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
# import torch
# import torchaudio
#
# MODEL_NAME = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
# MODEL = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME)
# FEATURE_EXTRACTOR = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
# MODEL.eval()


def detect_spoof(audio_bytes: bytes) -> dict:
    """
    Detect if audio is bonafide (real) or spoof (deepfake/replay/TTS).

    Args:
        audio_bytes: WAV audio (16kHz, mono)

    Returns:
        {"label": "bonafide" | "spoof", "confidence": float}
    """
    # === STUB (Phase 1) ===
    # Return random classification for testing
    # Bias toward bonafide for easier demo testing
    is_bonafide = random.random() > 0.3
    confidence = random.uniform(0.7, 0.99)

    return {
        "label": "bonafide" if is_bonafide else "spoof",
        "confidence": float(confidence)
    }

    # === REAL (Phase 2) ===
    # waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
    # if sample_rate != 16000:
    #     resampler = torchaudio.transforms.Resample(sample_rate, 16000)
    #     waveform = resampler(waveform)
    #
    # # Convert to mono if stereo
    # if waveform.shape[0] > 1:
    #     waveform = waveform.mean(dim=0, keepdim=True)
    #
    # inputs = FEATURE_EXTRACTOR(
    #     waveform.squeeze().numpy(),
    #     sampling_rate=16000,
    #     return_tensors="pt",
    #     padding=True
    # )
    #
    # with torch.no_grad():
    #     logits = MODEL(**inputs).logits
    #     probs = torch.softmax(logits, dim=-1)
    #     predicted_class = torch.argmax(probs, dim=-1).item()
    #     confidence = probs[0, predicted_class].item()
    #
    # # Class mapping depends on model training
    # # Typically: 0=bonafide, 1=spoof (verify with model card)
    # label = "bonafide" if predicted_class == 0 else "spoof"
    #
    # return {"label": label, "confidence": float(confidence)}
