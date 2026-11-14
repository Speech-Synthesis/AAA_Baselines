# AAA-ASR Day 2 — Public Dataset Research and Feasibility Report

**Author:** Nandan (Member 5 — AAA-ASR)  
**Date:** 14 November 2026  
**Repository:** `Speech-Synthesis/AAA_Baselines`  
**Branch:** `feat/nandan-asr-callguard-day2`  
**Classification:** PUBLIC-DATA EXPERIMENTAL TRACK (Separate from In-House Challenge Training)

---

## 1. Executive Summary & Objective

The objective of this investigation is to evaluate candidate public speech datasets for the **AAA-ASR Day 2 public-data baseline and fine-tuning experiment** while awaiting team-collected in-house challenge audio and signed consent documentation.

Per project constraints:
1. All local datasets, caches, temporary files, and deliverables remain strictly confined to the `E:` drive.
2. The public experiment must use openly accessible datasets with clear, verifiable licences.
3. The smallest practical dataset combination must be prioritized to avoid bandwidth exhaustion, unmanageable archive bloat, and prolonged iteration times.
4. The held-out test set must remain strictly preserved (touched once for final evaluation, never used for training or repeated hyperparameter tuning).
5. Public calibration data is strictly scoped to experimental confidence analysis and must not be conflated with final AAA challenge-response authentication thresholds.

---

## 2. Candidate Datasets Comparison Matrix

Below is the verified side-by-side analysis of candidate public datasets:

| Feature / Metric | LibriSpeech (`dev-clean`) | LibriSpeech (`train-clean-100`) | Google Speech Commands v2 | Mozilla Common Voice (EN) | MUSAN | RIRS_NOISES |
|---|---|---|---|---|---|---|
| **Official Source** | OpenSLR (SLR12) | OpenSLR (SLR12) | TensorFlow / Google Research | Mozilla Foundation | OpenSLR (SLR17) | OpenSLR (SLR28) |
| **Download URL** | `https://www.openslr.org/resources/12/dev-clean.tar.gz` | `https://www.openslr.org/resources/12/train-clean-100.tar.gz` | `https://storage.googleapis.com/download.tensorflow.org/data/speech_commands_v0.02.tar.gz` | `https://commonvoice.mozilla.org/en/datasets` | `https://www.openslr.org/resources/17/musan.tar.gz` | `https://www.openslr.org/resources/28/rirs_noises.zip` |
| **Release / Version** | SLR12 (dev-clean) | SLR12 (train-clean-100) | v0.02 (April 2018) | Release 17.0 / 18.0 / 27.0 | SLR17 | SLR28 |
| **Archive Download Size** | **337.9 MB** (322.2 MiB) | 6.38 GB (5.94 GiB) | 2.26 GB (2.43 GB uncompressed) | ~80+ GB (compressed EN) | 11.08 GB | 1.31 GB |
| **Number of Speakers** | 40 (20 M, 20 F) | 251 (126 M, 125 F) | 2,618 speakers | Thousands (unbalanced) | N/A (Crowdsourced / LibriVox) | N/A (Acoustic IRs) |
| **Number of Utterances** | 2,703 utterances (~5.4h) | 28,539 utterances (~100.6h) | 105,829 utterances (~29.4h) | > 1,000,000 utterances | ~109 hours | Simulated + real rooms |
| **Audio Format & Rate** | FLAC, 16 kHz, 16-bit mono | FLAC, 16 kHz, 16-bit mono | WAV, 16 kHz, 16-bit mono | MP3, 32/48 kHz, variable bit rate | WAV, 16 kHz, 16-bit mono | WAV, 16 kHz, 16-bit mono |
| **Utterance Duration** | 1.5s to 30.0s (mean: 7.2s) | 1.5s to 30.0s (mean: 12.7s) | Exactly 1.0s (fixed window) | 2.0s to 10.0s | 0.5s to several minutes | Impulse responses / Noise clips |
| **Transcript Availability** | Complete, standardized `.trans.txt` | Complete, standardized `.trans.txt` | Single-word class folders (verified) | Crowdsourced TSV text | None (Music, Speech, Noise) | None (Impulse responses) |
| **Licence** | **CC BY 4.0** | **CC BY 4.0** | **CC BY 4.0** | **CC0 1.0 Universal** | Mixed (CC BY 4.0, PD, US Govt) | **Apache License 2.0** |
| **Commercial Use** | Permitted (with attribution) | Permitted (with attribution) | Permitted (with attribution) | Permitted (public domain) | Permitted | Permitted |
| **Whisper Base Suitability** | Excellent (native 16 kHz, clean) | Excellent (native 16 kHz, clean) | Good for isolated tokens; boundary for duration | Requires MP3 decode + resampling | Noise-only augmentation | RIR acoustic simulation |
| **Primary Sprint Role** | **Train, Val, Cal, Test** (Baseline) | Large-scale pre-training | Short digit/command evaluation | Multi-accent evaluation | Background noise mixing | Room reverberation mixing |

---

## 3. In-Depth Evaluation of Candidates

### 3.1 LibriSpeech `dev-clean` (Selected Primary Candidate)
- **Strengths:**
  1. **Compact & Fast Acquisition:** At only 337.9 MB, it downloads rapidly and extracts cleanly on the `E:` drive without exhausting disk quota or network bandwidth.
  2. **Speaker Metadata Integrity:** Comes with official `SPEAKERS.TXT` metadata containing exact Speaker IDs, gender, and reading minutes.
  3. **Strict Speaker Disjointness:** Permits clean partitioning into 4 disjoint speaker subsets: Train (24 speakers), Validation (6 speakers), Calibration (4 speakers), and Held-Out Test (6 speakers).
  4. **Pristine Acoustic Quality:** 16 kHz FLAC lossless mono recording. Zero transcoding artifacts.
  5. **Direct Architectural Alignment:** Already designated in `02_MODEL_ARCHITECTURE/AAA-ASR.md` (Sections 10 & 15) as the official benchmark for replay regularization to monitor catastrophic forgetting.
- **Weaknesses:** Read speech from audiobooks; vocabulary is literary English rather than banking/challenge tokens.

### 3.2 LibriSpeech `train-clean-100`
- **Strengths:** 100 hours of high-quality speech; 251 distinct speakers.
- **Weaknesses:** Archive is 6.38 GB. Extracting and staging takes substantial time and storage on a rapid turnaround sprint. Best suited for high-compute cluster training rather than rapid Day 2 prototyping.

### 3.3 Google Speech Commands v2
- **Strengths:** 35 command words and digits ("zero" through "nine", "yes", "no", "stop", "go", etc.) that directly overlap with challenge phrase tokens. Includes a `_background_noise_` directory.
- **Weaknesses:** Archive is 2.26 GB. Utterances are strictly 1.0 second long, exactly at the lower boundary of `MIN_AUDIO_DURATION = 1.0s` specified in `SHARED.md` Section 2. Many samples are clipped at exactly 0.98s–1.00s.

### 3.4 Mozilla Common Voice English
- **Strengths:** Vast crowdsourced diversity, accents, and recording environments. CC0 licence.
- **Weaknesses:** Archive is over 80 GB compressed. Requires account/token login on Mozilla Data Collective or complex chunked web downloads. Audio is in variable-bitrate MP3 format requiring CPU-heavy decoding and resampling. Completely impractical for a lightweight initial experiment.

### 3.5 MUSAN & RIRS_NOISES
- **Strengths:** Industry standard for acoustic noise and reverberation augmentation.
- **Weaknesses:** Large archive sizes (MUSAN: 11.08 GB, RIRS_NOISES: 1.31 GB). Intended strictly for data augmentation rather than primary ASR transcription. Augmentation can be added modularly once clean baseline manifests are proven.

---

## 4. Recommendation for First Public Experiment

**Recommended Dataset Combination:**
- **Primary Core:** **LibriSpeech `dev-clean`** (337.9 MB).
- **Partitioning Strategy (Speaker-Disjoint):**
  - **Total:** 40 speakers (20 male, 20 female), 2,703 utterances.
  - **Train (`public_train.jsonl`):** 24 speakers (12 male, 12 female), ~1,620 utterances (~3.24 hours).
  - **Validation (`public_val.jsonl`):** 6 speakers (3 male, 3 female), ~405 utterances (~0.81 hours).
  - **Calibration (`public_cal.jsonl`):** 4 speakers (2 male, 2 female), ~270 utterances (~0.54 hours). Used exclusively for experimental confidence threshold analysis ($S_{exp}, \Delta$).
  - **Held-Out Test (`public_test.jsonl`):** 6 speakers (3 male, 3 female), ~408 utterances (~0.82 hours). Touched once during final evaluation.
- **Rationale:** This is the smallest practical, 100% reproducible, speaker-disjoint dataset available from official OpenSLR sources. It allows complete verification of the manifest pipeline, normalization logic, training loop, checkpoint export, and offline evaluation within Day 2 constraints.

### 4.1 Test Split Characterization and Future Scaling Note
- **Current Partition:** `public_test.jsonl` is an internal speaker-disjoint partition drawn from `dev-clean` (427 utterances, 6 speakers). It serves as an unviolated test gate to evaluate internal pipeline generalization and ensure the training loop does not overfit.
- **Future External Benchmark Recommendation:** Because `public_test.jsonl` originates from `dev-clean`, future benchmark evaluations requiring true out-of-split testing should incorporate the full `train-clean-100` (100 hours, 28,539 utterances) for production training and evaluate against the official `test-clean` (5.4 hours) benchmark.
