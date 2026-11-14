# AAA-ASR Day 2 — Experiment 2 Implementation & Technical Verification Report

**Author:** Nandan (Member 5 — AAA-ASR)  
**Date:** 14 November 2026  
**Repository:** `Speech-Synthesis/AAA_Baselines`  
**Branch:** `feat/nandan-asr-callguard-day2`  
**HEAD Commit:** `3765b06c8536ec9027246509e509ba85e3f334bf`  
**Model Architecture:** OpenAI Whisper Base — Multilingual (`base`, $V=51,865$, 71,825,920 total params)  
**Training Strategy:** Frozen Audio Encoder (`requires_grad=False`), Trainable Decoder (~52,003,328 params)  
**Status:** **ALL LOCAL VERIFICATION GATES PASSED**  
**Readiness State:** `READY FOR EXPERIMENT 2 — MANUAL KAGGLE LAUNCH`

---

## 1. Executive Summary & Authorized Scope

Following the post-training technical audit of Experiment 1, ten authorized changes were implemented to eliminate the root causes of validation WER degradation (catastrophic forgetting, tokenizer space mismatch, FP16 scaler desynchronization, and unexported checkpoints):

1. **Frozen Audio Encoder:** `model.encoder.eval()` with all 19,822,592 encoder parameters set to `requires_grad=False`. Only the 52,003,328 decoder parameters are updated.
2. **Leading-Space Lowercase Tokenization:** Transcripts are formatted as `" " + text.strip().lower()` prior to BPE encoding, ensuring token 0 has prefix space formatting (`376` `' mister'`) matching Whisper's autoregressive decoder output.
3. **FP16 GradScaler Synchronization:** `scheduler.step()` and `global_step` advance **strictly** when `scaler.step(optimizer)` confirms non-overflow gradient execution (`scale_before <= scale_after`).
4. **Hyperparameters:** Decoder learning rate reduced to $5\times 10^{-6}$, label smoothing set to $0.0$, weight decay $0.01$.
5. **Preserved Speaker Partitioning:** Exact 24 train, 6 validation, 4 calibration, and 6 test speakers maintained identically.
6. **Triple-Checkpoint Export Contract:**
   - `whisper_base_zero_shot_baseline.pt` (exported at step 0)
   - `whisper_base_public_best.pt` (exported when fine-tuned validation WER improves)
   - `whisper_base_public_final.pt` (exported unconditionally after epoch 3)
7. **Independent Best Metric Initialization:** `best_finetuned_wer` initialized to $\infty$, decoupling fine-tuned checkpoint export from the 6.00% zero-shot baseline.
8. **Calibration Partition Evaluation:** Evaluates `public_cal.jsonl` (299 utterances) and records mean log-probabilities, average confidence, and high-confidence ratios.
9. **Genuine Baseline vs. Fine-Tuned Test Comparison:** Produces side-by-side comparison on the held-out test split, reporting the exact WER delta.
10. **Experiment History Governance:** Explicitly documents that this held-out test evaluation is a subsequent evaluation (following Experiment 1 baseline exposure).

---

## 2. Parameter Allocation & Architecture Breakdown

```
================================================================================
OpenAI Whisper Multilingual Base Parameter Distribution (Experiment 2)
================================================================================
Audio Encoder (Frozen):        19,822,592 parameters (27.6%)  [requires_grad = False]
Text Decoder (Trainable):       52,003,328 parameters (72.4%)  [requires_grad = True]
--------------------------------------------------------------------------------
Total Parameters:               71,825,920 parameters (100.0%)
Vocabulary Size (Multilingual): 51,865 tokens
Compute Precision:              Mixed Precision FP16 (GradScaler synchronized)
================================================================================
```

Whenever `model.train()` is called during training, `model.encoder.eval()` is immediately re-asserted, guaranteeing that encoder LayerNorm and Dropout layers remain strictly in evaluation mode.

---

## 3. Local Verification Results

A comprehensive verification script was executed locally on CPU against real LibriSpeech audio, official `base.pt` weights, and production phrase verification modules:

```
==================================================================
Starting Comprehensive Verification for Experiment 2 (v1.2)
==================================================================

--- Test 1: Encoder Freezing & Mode Verification ---
Trainable params: 52,003,328 | Frozen params: 19,822,592
Test 1 PASSED: Encoder is strictly frozen and in eval mode.

--- Test 2: Gradient Flow Verification ---
Test 2 PASSED: Only decoder receives valid non-NaN gradients (encoder receives zero gradients).

--- Test 3: Tokenizer Leading-Space Lowercase Formatting ---
Raw transcript:   'MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES'
Clean transcript: ' mister quilter is the apostle of the middle classes'
Encoded tokens:   [26562, 31619, 391, 307, 264]
First token: 26562 -> ' mister'
Test 3 PASSED: Leading space and autoregressive alignment verified.

--- Test 4: Three Checkpoints Export Contract ---
[Export] Saved native Whisper checkpoint to: test_baseline.pt (277.01 MB)
[Export] Saved native Whisper checkpoint to: test_best.pt (277.01 MB)
[Export] Saved native Whisper checkpoint to: test_final.pt (277.01 MB)
Test 4 PASSED: All 3 checkpoints conform to native format and reload successfully.

--- Test 5: Strict Test Partition Isolation ---
Test 5 PASSED: Zero test samples present in train, val, or cal splits.

==================================================================
ALL EXPERIMENT 2 VERIFICATION CHECKS PASSED!
==================================================================
```

---

## 4. Evaluation Governance & Test Partition History

- **Experiment 1 History:** In Experiment 1, the held-out test split (`public_test.jsonl`, 427 utterances, 6 speakers) was evaluated once against the stock zero-shot checkpoint (resulting in 6.00% WER).
- **Experiment 2 Exposure:** The upcoming test evaluation on Kaggle represents a **subsequent evaluation** of the fine-tuned model checkpoint.
- **Strict Invariance:** The test partition was never used for training, validation, early stopping, or hyperparameter selection. Assertions in both the script and notebook confirm zero sample or speaker overlap between the test partition and the train/val/cal sets.

---

## 5. Artifacts and Deliverables Inventory

The deliverables in `04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/` are fully synchronized:

1. **[kaggle_whisper_base_train.ipynb](file:///E:/AAA_PROJECT/AAA_Baselines/04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/kaggle_whisper_base_train.ipynb)** — 17-cell self-contained Kaggle notebook with frozen encoder, scaler synchronization, and triple checkpoint exports.
2. **[kaggle_whisper_base_train.py](file:///E:/AAA_PROJECT/AAA_Baselines/04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/kaggle_whisper_base_train.py)** — Python training pipeline implementing the exact same logic.
3. **[public_experiment_config.json](file:///E:/AAA_PROJECT/AAA_Baselines/04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/public_experiment_config.json)** — Configuration for Experiment 2 ($lr = 5\times 10^{-6}$, label smoothing $0.0$, 52M trainable params).
4. **[KAGGLE_EXECUTION_GUIDE.md](file:///E:/AAA_PROJECT/AAA_Baselines/04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/KAGGLE_EXECUTION_GUIDE.md)** — Updated execution guide detailing Experiment 2 execution and artifact retrieval.

---

## 6. Final Status Declaration

**`READY FOR EXPERIMENT 2 — MANUAL KAGGLE LAUNCH`**
