# AAA-ASR Day 2 — Kaggle Public Experiment Execution Guide

**Author:** Nandan (Member 5 — AAA-ASR)  
**Date:** 14 November 2026  
**Repository:** `Speech-Synthesis/AAA_Baselines`  
**Track:** Public-Data Whisper Base v1.1 Fine-Tuning Experiment  
**Status:** READY FOR EXECUTION

---

## 1. Overview & Objectives

Because the local development environment is CPU-only (`torch 2.4.1+cpu`, CUDA unavailable), fine-tuning the 74M-parameter Whisper Base model must be executed on a cloud GPU accelerator (Kaggle NVIDIA T4 or P100).

This guide provides exact, reproducible steps to upload the public LibriSpeech `dev-clean` dataset, run the fine-tuning notebook, verify the native checkpoint export contract, and transfer the resulting model checkpoint back for local offline verification.

---

## 2. Prerequisites & Kaggle Environment Requirements

1. **Kaggle Account:** An active account at [kaggle.com](https://www.kaggle.com).
2. **Phone Verification:** Required by Kaggle to enable free GPU accelerators (30 hours/week). Go to `kaggle.com/settings` -> **Phone verification**.
3. **Accelerator Selection:** GPU T4 x2 or GPU P100.
4. **Internet Access Setting:** Enabled in notebook settings (required to install `openai-whisper` and download the initial base model weights).
5. **No Private Audio:** Strict project policy: **zero private or in-house voice data may be uploaded to Kaggle**. Only the public CC BY 4.0 LibriSpeech dataset is used.

---

## 3. Step-by-Step Execution Procedure

### Step 1: Self-Contained In-Notebook Dataset Staging
The notebook is 100% self-contained. You do **not** need to manually upload datasets or manifests to Kaggle.
Cell 2 in the notebook automatically downloads the 337.9 MB `dev-clean.tar.gz` archive directly from official OpenSLR SLR12, extracts audio under `./data/LibriSpeech`, and generates the 4 speaker-disjoint manifest files (`public_train.jsonl`, `public_val.jsonl`, `public_cal.jsonl`, `public_test.jsonl`) with verified Linux-compatible POSIX paths (`/kaggle/working/...`).

---

### Step 2: Create and Configure Kaggle Notebook

1. Navigate to [kaggle.com/code](https://www.kaggle.com/code) and click **New Notebook**.
2. Go to the right-hand **Notebook Options** panel:
   - **Accelerator:** Select `GPU T4 x2` or `GPU P100`.
   - **Language:** `Python`.
   - **Environment:** `Always use latest environment`.
   - **Internet:** Toggle to `ON` (required for OpenSLR download and Whisper dependencies).
3. Click **File** -> **Import Notebook** -> Select `kaggle_whisper_base_train.ipynb` from:
   `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\AAA_ASR\public_experiment\kaggle_whisper_base_train.ipynb`

---

### Step 3: Execute the Notebook (Experiment 2: Frozen Encoder v1.2)

Run all cells sequentially (`Run All` or `Shift + Enter` cell by cell):

1. **Cell 1 — Pre-Flight Hardware Gates:**
   - Verifies CUDA GPU presence and checks that available VRAM is $\ge 6.0$ GB.
   - Installs `openai-whisper`, `soundfile`, and `scipy`.
2. **Cell 2 — Dataset Staging & Linux Manifest Generation:**
   - Downloads `dev-clean.tar.gz` directly from OpenSLR (`https://www.openslr.org/resources/12/dev-clean.tar.gz`).
   - Extracts archive and parses transcripts.
   - Generates the 4 speaker-disjoint manifest splits reproducing the exact 24/6/4/6 speaker partitioning from `manifest_generator.py`.
   - Validates split counts (1544 / 433 / 299 / 427), checks zero speaker and sample leakage, and verifies Linux audio paths.
3. **Cell 3 — Metrics Implementation:**
   - Implements Levenshtein-based WER, CER, and Exact Phrase Accuracy (EPA).
4. **Cell 4 — Dataset Loading with Leading-Space Lowercase Formatting:**
   - Implements `WhisperSpeechDataset` with `" " + text.lower()` formatting to match Whisper BPE prefix expectation.
   - Autoregressive alignment (`dec_input = tokens[:-1]`, `target = tokens[1:]`, prompt masked with `-100`).
   - Dynamically pads collation batches using `tokenizer.eot` and `-100`.
5. **Cell 5 — Multilingual Model Loading & Audio Encoder Freezing:**
   - Loads official multilingual OpenAI Whisper `base` ($V=51,865$, 74M params).
   - Strictly freezes the audio encoder (`model.encoder.eval()`, `requires_grad=False`), keeping ~37.2M decoder parameters trainable.
   - Defines export function saving `{"dims": model.dims.__dict__, "model_state_dict": model.state_dict()}` for full compatibility with `whisper.load_model()`.
6. **Cell 6 — Evaluation Loop with Confidence Metrics:**
   - Implements beam/greedy decoding evaluation on validation, calibration, and test splits with token logprob extraction.
7. **Cell 7 — Training Execution (LR=5e-6, Scaler Synchronized):**
   - Asserts strict test set isolation.
   - Exports Checkpoint 1/3: `whisper_base_zero_shot_baseline.pt`.
   - Evaluates Stage 0 zero-shot baseline on `val` split.
   - Runs fine-tuning with AdamW on trainable parameters ($lr = 5\times 10^{-6}$, weight decay = $0.01$, label smoothing = $0.0$).
   - Advances scheduler and step counter strictly when `GradScaler` confirms successful updates (`scale_before <= scale_after`).
   - Evaluates validation WER every 50 optimizer steps and exports Checkpoint 2/3: `whisper_base_public_best.pt` whenever validation WER improves (initialized to $\infty$).
   - Exports Checkpoint 3/3: `whisper_base_public_final.pt` at epoch 3 completion.
8. **Cell 8 — Calibration & Baseline vs. Fine-Tuned Test Comparison:**
   - Evaluates `public_cal.jsonl` with token confidence / average logprob metrics.
   - Runs subsequent held-out test evaluation on both baseline and fine-tuned checkpoints, reporting the true delta.
   - Emits `PUBLIC_EXPERIMENT_METRICS.json` to `./output`.

---

### Step 4: Download Artifacts from Kaggle

After the notebook finishes:
1. In the right-hand pane under **Data** -> **Output** (`/kaggle/working/output`):
   - Locate `whisper_base_zero_shot_baseline.pt`
   - Locate `whisper_base_public_best.pt`
   - Locate `whisper_base_public_final.pt`
   - Locate `PUBLIC_EXPERIMENT_METRICS.json`
2. Click the three dots `...` next to each file and select **Download**.
3. Place the downloaded files in:
   - Checkpoints $\rightarrow$ `E:\AAA_PROJECT\AAA_Baselines\.models\whisper\`
   - `PUBLIC_EXPERIMENT_METRICS.json` $\rightarrow$ `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\AAA_ASR\public_experiment\PUBLIC_EXPERIMENT_METRICS.json`

---

### Step 5: Local Offline Verification Gate

Run the local offline verification script to confirm that the downloaded checkpoint loads seamlessly in the local `Transcriber` without network calls:

```powershell
# From E:\AAA_PROJECT\AAA_Baselines:
E:\AAA_PROJECT\AAA_Baselines\.venv\Scripts\python.exe -c "
import whisper
model = whisper.load_model('E:/AAA_PROJECT/AAA_Baselines/.models/whisper/whisper_base_public_best.pt')
print('Native Whisper checkpoint loaded successfully!')
print('Model dims:', model.dims)
"
```
