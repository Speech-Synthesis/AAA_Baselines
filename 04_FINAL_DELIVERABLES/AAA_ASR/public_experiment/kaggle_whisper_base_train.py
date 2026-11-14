"""
Kaggle Whisper Base Multilingual Fine-Tuning — Experiment 2 (Frozen Encoder v1.2)
Author: Nandan (Member 5 — AAA-ASR)
Date: 14 November 2026
Repository: Speech-Synthesis/AAA_Baselines
Track: Public Dataset Baseline (LibriSpeech dev-clean)

Key Changes in Experiment 2:
1. Frozen audio encoder (model.encoder.eval(), requires_grad=False). Only decoder is trained (~37.2M params).
2. Transcript tokenization: clean leading space (" " + text.lower()) matching Whisper BPE prefix expectation.
3. FP16 GradScaler synchronization: scheduler and global_step advance ONLY when scaler.step(optimizer) succeeds.
4. Hyperparameters: decoder learning rate 5e-6, label smoothing 0.0, weight decay 0.01.
5. Three distinct checkpoints exported:
   - whisper_base_zero_shot_baseline.pt
   - whisper_base_public_best.pt
   - whisper_base_public_final.pt
6. Independent best fine-tuned validation WER tracking (initialized to inf).
7. Dedicated calibration partition evaluation with confidence metrics.
8. Baseline vs. fine-tuned held-out test comparison with documented evaluation governance.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.signal
import soundfile as sf
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import whisper
from whisper.tokenizer import get_tokenizer


# -----------------------------------------------------------------------------
# 1. Normalization & Metrics Implementation
# -----------------------------------------------------------------------------

FILLER_WORDS = frozenset({"um", "uh", "er", "hmm", "erm", "ah"})
DIGIT_TO_WORD = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
    "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen",
    "18": "eighteen", "19": "nineteen", "20": "twenty", "21": "twenty one",
    "30": "thirty", "40": "forty", "50": "fifty", "60": "sixty",
    "70": "seventy", "80": "eighty", "90": "ninety",
}
WORD_ALIASES = {"oh": "zero"}
SPELLING_MAP = {
    "colour": "color", "favourite": "favorite", "grey": "gray",
    "licence": "license", "defence": "defense", "catalogue": "catalog",
    "centre": "center", "metre": "meter", "litre": "liter",
    "analyse": "analyze", "organise": "organize", "recognise": "recognize",
    "realise": "realize", "apologise": "apologize",
}
CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not",
    "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
    "i'm": "i am", "you're": "you are", "we're": "we are",
    "they're": "they are", "he's": "he is", "she's": "she is",
    "it's": "it is", "i've": "i have", "you've": "you have",
    "we've": "we have", "they've": "they have", "i'll": "i will",
    "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "i'd": "i would", "you'd": "you would", "we'd": "we would",
    "they'd": "they would", "let's": "let us",
}


def normalize_text(text: str) -> str:
    """Normalize text matching official AAA-ASR phrase_matcher rules."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text).lower().strip()
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(r"\b" + re.escape(contraction) + r"\b", expansion, text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()

    words = [w for w in text.split() if w not in FILLER_WORDS]
    normalized = []
    for word in words:
        if word in DIGIT_TO_WORD:
            normalized.extend(DIGIT_TO_WORD[word].split())
        else:
            normalized.append(word)

    words = [SPELLING_MAP.get(w, w) for w in normalized]
    words = [WORD_ALIASES.get(w, w) for w in words]
    return " ".join(words)


def compute_levenshtein(seq1: list | str, seq2: list | str) -> int:
    n1, n2 = len(seq1), len(seq2)
    dp = [[0] * (n2 + 1) for _ in range(n1 + 1)]
    for i in range(n1 + 1):
        dp[i][0] = i
    for j in range(n2 + 1):
        dp[0][j] = j
    for i in range(1, n1 + 1):
        for j in range(1, n2 + 1):
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[n1][n2]


def compute_metrics(predictions: list[str], references: list[str]) -> dict[str, float]:
    """Calculate WER, CER, and Exact Phrase Accuracy (EPA)."""
    total_word_dist = 0
    total_ref_words = 0
    total_char_dist = 0
    total_ref_chars = 0
    exact_matches = 0
    n = len(predictions)

    for p, r in zip(predictions, references):
        norm_p = normalize_text(p)
        norm_r = normalize_text(r)

        if norm_p == norm_r:
            exact_matches += 1

        p_words = norm_p.split()
        r_words = norm_r.split()
        total_word_dist += compute_levenshtein(p_words, r_words)
        total_ref_words += max(len(r_words), 1)

        total_char_dist += compute_levenshtein(norm_p, norm_r)
        total_ref_chars += max(len(norm_r), 1)

    wer = (total_word_dist / total_ref_words) * 100.0 if total_ref_words > 0 else 0.0
    cer = (total_char_dist / total_ref_chars) * 100.0 if total_ref_chars > 0 else 0.0
    epa = (exact_matches / n) * 100.0 if n > 0 else 0.0

    return {
        "wer": round(wer, 2),
        "cer": round(cer, 2),
        "exact_phrase_accuracy": round(epa, 2),
        "total_evaluated": n,
        "exact_matches": exact_matches,
    }


# -----------------------------------------------------------------------------
# 2. Dataset & Collate Function (With Leading-Space Tokenization)
# -----------------------------------------------------------------------------

class WhisperSpeechDataset(Dataset):
    """
    Dataset loading audio, resampling to 16kHz, and preparing correctly shifted
    autoregressive token sequences with standard BPE leading space.
    """

    def __init__(self, manifest_path: Path, tokenizer, is_train: bool = True):
        self.records = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.records.append(json.loads(line))
        self.tokenizer = tokenizer
        self.is_train = is_train

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        audio_path = rec["audio_path"]
        transcript = rec["transcript"]

        audio, sr = sf.read(audio_path, dtype="float32")
        if audio.size == 0:
            raise ValueError(f"Empty audio file encountered: {audio_path}")

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sr != 16000:
            target_len = int(round(len(audio) * 16000.0 / sr))
            audio = scipy.signal.resample(audio, target_len).astype(np.float32)
            sr = 16000

        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio)

        # Prepend a leading space and lowercase text matching Whisper BPE formatting
        clean_text = " " + transcript.strip().lower()
        prompt_tokens = list(self.tokenizer.sot_sequence_including_notimestamps)
        text_tokens = self.tokenizer.encode(clean_text)
        eot = self.tokenizer.eot

        tokens = prompt_tokens + text_tokens + [eot]

        # Teacher-forced autoregressive alignment:
        # dec_input: tokens[:-1]
        # target:    tokens[1:]
        dec_input = torch.tensor(tokens[:-1], dtype=torch.long)
        target = torch.tensor(tokens[1:], dtype=torch.long)

        # Mask prompt tokens in target with -100
        target[: len(prompt_tokens) - 1] = -100

        return {
            "mel": mel,
            "dec_input": dec_input,
            "target": target,
            "transcript": transcript,
            "sample_id": rec["sample_id"]
        }


def make_collate_fn(tokenizer):
    """Dynamic padding collate function using tokenizer EOT pad token."""
    pad_token_id = tokenizer.eot

    def collate_fn(batch):
        mels = torch.stack([item["mel"] for item in batch])
        max_len = max(len(item["dec_input"]) for item in batch)

        dec_inputs = []
        targets = []
        for item in batch:
            pad_len = max_len - len(item["dec_input"])
            dec_input = torch.cat([
                item["dec_input"],
                torch.full((pad_len,), pad_token_id, dtype=torch.long)
            ])
            target = torch.cat([
                item["target"],
                torch.full((pad_len,), -100, dtype=torch.long)
            ])
            dec_inputs.append(dec_input)
            targets.append(target)

        return {
            "mel": mels,
            "dec_input": torch.stack(dec_inputs),
            "target": torch.stack(targets),
            "transcripts": [item["transcript"] for item in batch],
            "sample_ids": [item["sample_id"] for item in batch]
        }

    return collate_fn


# -----------------------------------------------------------------------------
# 3. Evaluation Function with Confidence Metrics
# -----------------------------------------------------------------------------

def evaluate_model(model, dataloader, tokenizer, device, record_confidence: bool = False) -> dict[str, float]:
    """Run evaluation and decode predictions for metrics and confidence calculation."""
    model.eval()
    predictions = []
    references = []
    avg_logprobs = []

    with torch.no_grad():
        for batch in dataloader:
            mels = batch["mel"].to(device)
            options = whisper.DecodingOptions(
                language="en",
                task="transcribe",
                without_timestamps=True,
                beam_size=1,
                fp16=(device.type == "cuda")
            )
            results = model.decode(mels, options)
            for res, ref in zip(results, batch["transcripts"]):
                predictions.append(res.text)
                references.append(ref)
                if record_confidence:
                    avg_logprobs.append(res.avg_logprob)

    metrics = compute_metrics(predictions, references)
    if record_confidence and avg_logprobs:
        mean_logprob = float(np.mean(avg_logprobs))
        metrics["mean_avg_logprob"] = round(mean_logprob, 4)
        metrics["mean_confidence"] = round(float(np.exp(mean_logprob)), 4)
        metrics["high_confidence_ratio"] = round(float(np.mean([1.0 if lp > -0.5 else 0.0 for lp in avg_logprobs])) * 100.0, 2)

    return metrics


# -----------------------------------------------------------------------------
# 4. Native Checkpoint Export Contract & Scheduler
# -----------------------------------------------------------------------------

def export_native_whisper_checkpoint(model, output_path: Path):
    """Save model adhering strictly to OpenAI Whisper native format with dims as dict."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "dims": model.dims.__dict__,
        "model_state_dict": model.state_dict()
    }
    torch.save(checkpoint, output_path)
    print(f"[Export] Saved native Whisper checkpoint to: {output_path} ({output_path.stat().st_size / (1024**2):.2f} MB)")


def create_cosine_lr_scheduler(optimizer, warmup_steps: int, total_steps: int, min_lr_ratio: float = 0.01):
    """Linear warmup followed by cosine annealing learning rate scheduler."""
    def lr_lambda(current_step: int):
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return max(min_lr_ratio, cosine_decay)

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# -----------------------------------------------------------------------------
# 5. Main Training Pipeline
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Kaggle Whisper Base Multilingual Fine-Tuning (Experiment 2)")
    parser.add_argument("--config", type=str, default="public_experiment_config.json")
    parser.add_argument("--manifest-dir", type=str, default=".")
    parser.add_argument("--output-dir", type=str, default="output")
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Setup] Active compute device: {device}")

    # 1. Load Multilingual Base Model and Freeze Audio Encoder
    base_model_name = config["model_specification"].get("base_checkpoint", "base")
    print(f"[Model] Loading native OpenAI Whisper: {base_model_name} (Multilingual Base, V=51865) ...")
    model = whisper.load_model(base_model_name, device=device)

    # Freeze audio encoder
    model.encoder.eval()
    for param in model.encoder.parameters():
        param.requires_grad = False

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen_params = sum(p.numel() for p in model.parameters() if not p.requires_grad)
    print(f"[Model] Trainable parameters (Decoder only): {trainable_params:,} ({trainable_params/74000000*100:.1f}%)")
    print(f"[Model] Frozen parameters (Audio Encoder):   {frozen_params:,} ({frozen_params/74000000*100:.1f}%)")

    tokenizer = get_tokenizer(multilingual=True, language="en", task="transcribe")
    collate_fn = make_collate_fn(tokenizer)

    # 2. Create Datasets and DataLoaders
    train_manifest = manifest_dir / config["dataset_configuration"]["manifests"]["train"]
    val_manifest = manifest_dir / config["dataset_configuration"]["manifests"]["val"]
    cal_manifest = manifest_dir / config["dataset_configuration"]["manifests"]["cal"]
    test_manifest = manifest_dir / config["dataset_configuration"]["manifests"]["test"]

    train_ds = WhisperSpeechDataset(train_manifest, tokenizer, is_train=True)
    val_ds = WhisperSpeechDataset(val_manifest, tokenizer, is_train=False)
    cal_ds = WhisperSpeechDataset(cal_manifest, tokenizer, is_train=False)
    test_ds = WhisperSpeechDataset(test_manifest, tokenizer, is_train=False)

    # Invariant: Zero leakage check with held-out test set
    train_ids = set(r["sample_id"] for r in train_ds.records)
    val_ids = set(r["sample_id"] for r in val_ds.records)
    cal_ids = set(r["sample_id"] for r in cal_ds.records)
    test_ids = set(r["sample_id"] for r in test_ds.records)

    assert len(train_ids.intersection(test_ids)) == 0, "FATAL: Test samples leaked into train split!"
    assert len(val_ids.intersection(test_ids)) == 0, "FATAL: Test samples leaked into val split!"
    assert len(cal_ids.intersection(test_ids)) == 0, "FATAL: Test samples leaked into cal split!"

    batch_size = config["training_hyperparameters"]["batch_size_per_device"]
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn, num_workers=2)
    cal_loader = DataLoader(cal_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn, num_workers=2)

    print(f"[Data] Train: {len(train_ds)} utts | Val: {len(val_ds)} | Cal: {len(cal_ds)} | Held-Out Test: {len(test_ds)}")

    # 3. Export Baseline Checkpoint (Checkpoint 1/3)
    baseline_ckpt_path = output_dir / "whisper_base_zero_shot_baseline.pt"
    export_native_whisper_checkpoint(model, baseline_ckpt_path)

    # 4. Baseline Zero-Shot Evaluation (Stage 0 Baseline)
    print("\n--- Running Stage 0 Stock Whisper Multilingual Baseline on Val Set ---")
    val_baseline = evaluate_model(model, val_loader, tokenizer, device)
    print(f"[Stage 0 Baseline Val] WER: {val_baseline['wer']}% | CER: {val_baseline['cer']}% | EPA: {val_baseline['exact_phrase_accuracy']}%")

    # 5. Setup Optimizer, LR Scheduler & GradScaler
    hparams = config["training_hyperparameters"]
    grad_accum = hparams["gradient_accumulation_steps"]
    max_epochs = hparams["max_epochs"]

    batches_per_epoch = len(train_loader)
    optimizer_updates_per_epoch = math.ceil(batches_per_epoch / grad_accum)
    total_optimizer_steps = optimizer_updates_per_epoch * max_epochs
    warmup_steps = hparams.get("warmup_steps", int(round(total_optimizer_steps * 0.12)))

    # Only optimize trainable parameters
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=hparams["learning_rate"],
        weight_decay=hparams["weight_decay"],
        betas=tuple(hparams["betas"]),
        eps=hparams.get("eps", 1e-8)
    )
    scheduler = create_cosine_lr_scheduler(optimizer, warmup_steps=warmup_steps, total_steps=total_optimizer_steps)
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100, label_smoothing=hparams["label_smoothing"])
    scaler = torch.cuda.amp.GradScaler(enabled=(hparams["mixed_precision"] == "fp16" and device.type == "cuda"))

    # Best fine-tuned WER initialized independently of zero-shot baseline
    best_finetuned_wer = float("inf")
    best_checkpoint_path = output_dir / "whisper_base_public_best.pt"
    final_checkpoint_path = output_dir / "whisper_base_public_final.pt"

    # 6. Fine-Tuning Loop with Correct GradScaler Step Synchronization
    print(f"\n--- Starting Experiment 2 Fine-Tuning (Frozen Encoder, LR={hparams['learning_rate']:.1e}) ---")
    global_step = 0
    successful_updates = 0
    skipped_updates = 0
    start_time = time.time()
    accum_loss = 0.0
    accum_count = 0

    model.train()
    model.encoder.eval()  # Keep encoder strictly in eval mode
    optimizer.zero_grad()

    for epoch in range(max_epochs):
        print(f"\n>>> Epoch {epoch + 1}/{max_epochs} <<<")
        for batch_idx, batch in enumerate(train_loader):
            mels = batch["mel"].to(device)
            dec_inputs = batch["dec_input"].to(device)
            targets = batch["target"].to(device)

            is_last_batch = (batch_idx + 1 == batches_per_epoch)
            is_accum_step = ((batch_idx + 1) % grad_accum == 0) or is_last_batch

            with torch.cuda.amp.autocast(enabled=(hparams["mixed_precision"] == "fp16" and device.type == "cuda")):
                logits = model(mels, dec_inputs)
                raw_loss = loss_fn(logits.view(-1, logits.size(-1)), targets.view(-1))

            accum_count += 1
            accum_loss += raw_loss.item()
            loss = raw_loss / (accum_count if is_accum_step else grad_accum)
            scaler.scale(loss).backward()

            if is_accum_step:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(filter(lambda p: p.requires_grad, model.parameters()), hparams["gradient_clipping"])

                scale_before = scaler.get_scale()
                scaler.step(optimizer)
                scaler.update()
                scale_after = scaler.get_scale()

                # Step scheduler and increment global_step ONLY if optimizer actually stepped
                if scale_before <= scale_after:
                    successful_updates += 1
                    scheduler.step()
                    global_step += 1
                else:
                    skipped_updates += 1
                    print(f"  [AMP WARNING] Gradient overflow at batch {batch_idx}. Step skipped! Scale: {scale_before:.1f} -> {scale_after:.1f}")

                current_lr = optimizer.param_groups[0]["lr"]
                avg_group_loss = accum_loss / accum_count
                accum_loss = 0.0
                accum_count = 0
                optimizer.zero_grad()

                if global_step % 20 == 0 or global_step == 1:
                    print(f"  Step {global_step:3d}/{total_optimizer_steps} | Loss: {avg_group_loss:.4f} | LR: {current_lr:.2e} | Updates: {successful_updates} | Skipped: {skipped_updates}")

                eval_interval = config["validation_and_early_stopping"]["eval_interval_steps"]
                if global_step > 0 and global_step % eval_interval == 0:
                    print(f"\n--- Validation at Step {global_step} ---")
                    val_metrics = evaluate_model(model, val_loader, tokenizer, device)
                    print(f"  [Val Eval] WER: {val_metrics['wer']}% | CER: {val_metrics['cer']}% | EPA: {val_metrics['exact_phrase_accuracy']}%")

                    if val_metrics["wer"] < best_finetuned_wer:
                        best_finetuned_wer = val_metrics["wer"]
                        print(f"  [Checkpoint 2/3] New best fine-tuned validation WER: {best_finetuned_wer}%! Saving best checkpoint ...")
                        export_native_whisper_checkpoint(model, best_checkpoint_path)

                    model.train()
                    model.encoder.eval()

    elapsed_min = (time.time() - start_time) / 60.0
    print(f"\n[Training Complete] Elapsed time: {elapsed_min:.2f} min | Successful Updates: {successful_updates} | Skipped: {skipped_updates}")

    # Export Final Checkpoint (Checkpoint 3/3)
    print("\n--- Exporting Final Checkpoint ---")
    export_native_whisper_checkpoint(model, final_checkpoint_path)

    # 7. Calibration Set Evaluation with Confidence Metrics
    eval_model_path = best_checkpoint_path if best_checkpoint_path.exists() else final_checkpoint_path
    print(f"\n--- Running Public Calibration Set Evaluation with {eval_model_path.name} ---")
    eval_model = whisper.load_model(str(eval_model_path), device=device)
    cal_metrics = evaluate_model(eval_model, cal_loader, tokenizer, device, record_confidence=True)
    print(f"[Cal Set Metrics] WER: {cal_metrics['wer']}% | Mean Logprob: {cal_metrics.get('mean_avg_logprob')} | Mean Conf: {cal_metrics.get('mean_confidence')}")

    # 8. Held-Out Test Evaluation (Subsequent Test Evaluation)
    print("\n--- RUNNING SUBSEQUENT HELD-OUT TEST EVALUATION ---")
    print("[Governance Note] Baseline test evaluation was established in Experiment 1. This is a subsequent evaluation of the fine-tuned model.")
    baseline_model = whisper.load_model(str(baseline_ckpt_path), device=device)
    baseline_test_metrics = evaluate_model(baseline_model, test_loader, tokenizer, device)
    finetuned_test_metrics = evaluate_model(eval_model, test_loader, tokenizer, device)

    print(f"[Baseline Test]  WER: {baseline_test_metrics['wer']}% | CER: {baseline_test_metrics['cer']}% | EPA: {baseline_test_metrics['exact_phrase_accuracy']}%")
    print(f"[Fine-Tuned Test] WER: {finetuned_test_metrics['wer']}% | CER: {finetuned_test_metrics['cer']}% | EPA: {finetuned_test_metrics['exact_phrase_accuracy']}%")
    wer_delta = round(finetuned_test_metrics["wer"] - baseline_test_metrics["wer"], 2)
    print(f"[Test Delta] WER Change: {wer_delta:+0.2f}%")

    # 9. Write Comprehensive Metrics Deliverable
    gpu_label = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    final_report = {
        "experiment_name": config["experiment_name"],
        "experiment_version": config["version"],
        "training_strategy": config["model_specification"]["training_strategy"],
        "hardware": gpu_label,
        "elapsed_training_minutes": round(elapsed_min, 2),
        "training_dynamics": {
            "total_steps_planned": total_optimizer_steps,
            "successful_optimizer_updates": successful_updates,
            "skipped_optimizer_updates": skipped_updates,
            "final_lr": optimizer.param_groups[0]["lr"]
        },
        "checkpoints_exported": {
            "zero_shot_baseline": str(baseline_ckpt_path.name),
            "best_fine_tuned": str(best_checkpoint_path.name) if best_checkpoint_path.exists() else None,
            "final_epoch_checkpoint": str(final_checkpoint_path.name)
        },
        "zero_shot_baseline_val": val_baseline,
        "best_fine_tuned_val_wer": best_finetuned_wer,
        "calibration_metrics": cal_metrics,
        "held_out_test_comparison": {
            "baseline_test_wer": baseline_test_metrics["wer"],
            "finetuned_test_wer": finetuned_test_metrics["wer"],
            "wer_delta": wer_delta,
            "baseline_metrics": baseline_test_metrics,
            "finetuned_metrics": finetuned_test_metrics
        },
        "governance": {
            "test_evaluation_history": "Experiment 1 ran baseline zero-shot evaluation. Experiment 2 evaluates the fine-tuned model as subsequent evaluation. Test set was not used for model selection."
        }
    }

    metrics_output_file = output_dir / "PUBLIC_EXPERIMENT_METRICS.json"
    with open(metrics_output_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)
    print(f"\n[Deliverable] Metrics report saved to: {metrics_output_file}")


if __name__ == "__main__":
    main()
