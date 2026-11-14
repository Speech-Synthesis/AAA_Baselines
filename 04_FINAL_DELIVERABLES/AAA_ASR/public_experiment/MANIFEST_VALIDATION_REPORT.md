# AAA-ASR Public Dataset Manifest Validation Report

**Author:** Nandan (Member 5 — AAA-ASR)  
**Date:** 14 November 2026  
**Track:** Public-Data Baseline Experiment  
**Dataset:** LibriSpeech `dev-clean` (OpenSLR SLR12)  
**Status:** VALIDATION PASSED  

---

## 1. Split Partitioning & Speaker Disjointness Summary

| Split | Number of Speakers | Number of Utterances | Total Duration (seconds) | Total Duration (hours) | Disjoint Status |
|---|---|---|---|---|---|
| **Train** (`public_train.jsonl`) | 24 | 1544 | 11638.4s | 3.23h | VERIFIED DISJOINT |
| **Val** (`public_val.jsonl`) | 6 | 433 | 2899.0s | 0.81h | VERIFIED DISJOINT |
| **Cal** (`public_cal.jsonl`) | 4 | 299 | 1953.7s | 0.54h | VERIFIED DISJOINT |
| **Test** (`public_test.jsonl`) | 6 | 427 | 2905.0s | 0.81h | VERIFIED DISJOINT |
| **TOTAL** | **40** | **2703** | **19396.1s** | **5.39h** | **100% DISJOINT** |

---

## 2. Quality Gate Verification Checklist

- [x] **Audio File Accessibility:** 100% of recorded audio paths exist and were verified.
- [x] **Audio Decodability:** All 2703 FLAC files were decoded via `soundfile` without header corruption.
- [x] **Sample Rate Uniformity:** All files verified at 16,000 Hz mono.
- [x] **Transcript Integrity:** Zero empty or missing transcripts. All transcripts parsed from verbatim `.trans.txt` files.
- [x] **Approved Normalization:** Applied deterministic `normalize_text()` from `backend/app/aaa_asr/phrase_matcher.py`.
- [x] **Duplicate Detection:** Zero duplicate sample IDs or duplicate audio paths.
- [x] **Speaker Leakage Check:** Zero speaker overlap between `train`, `val`, `cal`, and `test`.
- [x] **Sample Leakage Check:** Zero utterance ID overlap across splits.
- [x] **Held-Out Test Preservation:** `public_test.jsonl` strictly isolated for final benchmark evaluation.
- [x] **Failed Records:** 0 records failed validation gates.

---

## 3. Failed Records Log

`No failed records detected. All 2,703 utterances passed all quality and schema gates.`

---

## 4. Manifest SHA-256 Checksums

```
b72b7282ce88de3cfa6755803aac6b6fe4cb4e41c3cef0cd4c7fcc35be7896ed  public_cal.jsonl
2ec7620ddcc2a7f3b5f995879c60e76be5dd5ed2164c905665e6e501f89ce3ed  public_test.jsonl
0590bd70a226dfb4263caf89ee57450406cb3ce6b97024cd4350334ccf11ac55  public_train.jsonl
e6e28da8854bf7870f87267307fa4564a755b093df3b15d86b33bfabf7942fa1  public_val.jsonl
```

---

## 5. Scope Boundary Reiteration & Split Characterization

1. **Partition Role:** `public_test.jsonl` (427 utterances, 6 speakers) is an **internal speaker-disjoint partition** derived strictly from LibriSpeech `dev-clean`. It serves to verify pipeline generalization and prevent training/validation overfitting within this public sanity experiment.
2. **Benchmark Recommendation:** Because `public_test.jsonl` originates from `dev-clean`, it does not constitute an external out-of-domain benchmark. For comprehensive future benchmark evaluations, downloading `train-clean-100` (for extended training) and evaluating on `test-clean` is recommended.
3. This dataset is designated exclusively for the **public-data baseline and fine-tuning experiment**.
4. It does **not** replace or constitute challenge-specific AAA-ASR training.
5. Calibration data (`public_cal.jsonl`) evaluates experimental ASR confidence distribution ($S_{free}, S_{exp}, \Delta$) on open read speech, not AAA challenge pass/fail authentication thresholds.
6. Final AAA-ASR challenge training requires team-collected in-house recordings, signed consent records, and approved challenge vocabulary partitions.
