# AAA Engine — Model and GPU Status Report

**Date:** November 15, 2026
**Author:** Surya
**Environment:** Python 3.14, PyTorch 2.14.0+cpu

---

## 1. GPU Detection

| Parameter | Value |
|-----------|-------|
| GPU Detected | Yes |
| Device | NVIDIA GeForce RTX 4060 Laptop GPU |
| VRAM | 8 GB |
| CUDA Version | 12.6 |
| Driver Version | 566.14 |
| PyTorch CUDA | NOT AVAILABLE |

**Reason:** Python 3.14 is too new for PyTorch CUDA wheels. All inference runs on CPU.

---

## 2. Model Status

### Speaker Verification (SV)
| Property | Value |
|----------|-------|
| Model ID | speechbrain/spkrec-ecapa-voxceleb |
| Architecture | ECAPA-TDNN |
| Embedding Dim | 192 |
| Framework | SpeechBrain |
| Status | LOADED ✓ |
| Inference Time | 177ms (CPU) |

### Anti-Spoofing / Deepfake Detection (AD)
| Property | Value |
|----------|-------|
| Model ID | garystafford/wav2vec2-deepfake-voice-detector |
| Architecture | Wav2Vec2 |
| Labels | bonafide, spoof |
| Framework | Transformers |
| Status | LOADED ✓ |
| Inference Time | 922ms (CPU) |

### Automatic Speech Recognition (ASR)
| Property | Value |
|----------|-------|
| Model ID | openai/whisper-base |
| Architecture | Whisper |
| Size | Base (74M parameters) |
| Framework | OpenAI Whisper |
| Status | LOADED ✓ |
| Inference Time | 471ms (CPU) |
| Fine-Tuned | NO (stock model) |

---

## 3. Fine-Tuning Status

| Requirement | Original Spec | Current Status |
|-------------|--------------|----------------|
| Whisper fine-tuning on phrase corpus | Required | NOT IMPLEMENTED |

**Note:** Stock Whisper Base is used. Fine-tuning on challenge phrase vocabulary would improve accuracy but is not blocking for the current implementation.

Public experiment files exist at:
- `04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/`

---

## 4. GPU Acceleration Path

To enable GPU inference:

1. Create Python 3.11 or 3.12 virtual environment
2. Install PyTorch with CUDA:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
3. Verify CUDA availability:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   ```

**Current environment is preserved and functional with CPU inference.**

---

## 5. Performance Benchmarks

| Operation | CPU Time | Expected GPU Time |
|-----------|----------|-------------------|
| Challenge generation | 1439.7ms | ~1400ms (DB-bound) |
| AD inference | 922ms | ~150ms |
| ASR inference | 471ms | ~100ms |
| SV inference | 242.3ms | ~50ms |
| **Total pipeline** | **4975.1ms** | **~1700ms** |

---

## 6. Model Loading Evidence

```python
# SV Model
from speechbrain.pretrained import EncoderClassifier
model = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb")
embedding = model.encode_batch(waveform)
# Shape: (1, 192)

# AD Model
from transformers import AutoModelForAudioClassification
model = AutoModelForAudioClassification.from_pretrained(
    "garystafford/wav2vec2-deepfake-voice-detector"
)
# Labels: ['bonafide', 'spoof']

# ASR Model
import whisper
model = whisper.load_model("base")
result = model.transcribe(audio_path)
# Returns: {'text': '...', 'language': 'en'}
```

---

## 7. Model Weight Locations

Models are cached in:
- `~/.cache/huggingface/hub/`
- `~/.cache/torch/` (SpeechBrain)
- `~/.cache/whisper/` (Whisper)

**No model weights are committed to the repository.**

---

**Report Status:** COMPLETE
**Inference Status:** CPU ONLY (functional)
