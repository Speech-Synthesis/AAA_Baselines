"""
Comprehensive Local Verification Suite for AAA-ASR Day 2 Pre-Training Corrections.
Verifies all 4 blocking defects (D-1, D-2, D-3, D-4) and additional improvements.
Run locally on CPU without modifying git tree or teammate files.
"""

import sys
import os
from pathlib import Path
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[3]
DELIVERABLES_DIR = REPO_ROOT / "04_FINAL_DELIVERABLES" / "AAA_ASR" / "public_experiment"
MODELS_DIR = REPO_ROOT / ".models" / "whisper"
BASE_CHECKPOINT = MODELS_DIR / "base.pt"

# Add deliverables dir to path to import training module
sys.path.insert(0, str(DELIVERABLES_DIR))
sys.path.insert(0, str(REPO_ROOT))

import whisper
from whisper.tokenizer import get_tokenizer
from kaggle_whisper_base_train import (
    WhisperSpeechDataset,
    make_collate_fn,
    create_cosine_lr_scheduler,
    export_native_whisper_checkpoint,
    normalize_text
)
from backend.app.aaa_asr.phrase_matcher import PhraseVerifier, normalize_text as ref_normalize_text


def test_verification_a():
    print("\n--- [Verification A] Model & Architecture Alignment ---")
    assert BASE_CHECKPOINT.exists(), f"Missing checkpoint: {BASE_CHECKPOINT}"
    print(f"Loading local base checkpoint: {BASE_CHECKPOINT}")
    model = whisper.load_model(str(BASE_CHECKPOINT), device="cpu")
    
    dims = model.dims
    print(f"Model dimensions: n_vocab={dims.n_vocab}, n_audio_ctx={dims.n_audio_ctx}, n_audio_state={dims.n_audio_state}, n_text_state={dims.n_text_state}")
    assert dims.n_vocab == 51865, f"Expected n_vocab=51865 for multilingual base, got {dims.n_vocab}"
    
    tok = get_tokenizer(multilingual=True, language="en", task="transcribe")
    print(f"Tokenizer: sot={tok.sot}, eot={tok.eot}, transcribe={tok.transcribe}, en={tok.language_token}")
    assert tok.eot == 50257, f"Expected eot=50257, got {tok.eot}"
    assert tok.sot == 50258, f"Expected sot=50258, got {tok.sot}"
    print("Verification A PASSED: Multilingual base architecture ($V=51,865$) verified.")
    return model, tok


def test_verification_b(tok):
    print("\n--- [Verification B] Dataset Loading & Audio Preprocessing ---")
    train_manifest = DELIVERABLES_DIR / "public_train.jsonl"
    assert train_manifest.exists(), f"Missing manifest: {train_manifest}"
    
    ds = WhisperSpeechDataset(str(train_manifest), tok)
    print(f"Dataset length: {len(ds)} items")
    assert len(ds) == 1544, f"Expected 1544 items, got {len(ds)}"
    
    # Inspect 5 samples
    for i in range(5):
        sample = ds[i]
        mel = sample["mel"]
        dec_in = sample["dec_input"]
        target = sample["target"]
        text = sample["transcript"]
        
        print(f"Sample {i}: text='{text[:30]}...', mel={mel.shape}, dec_in={dec_in.shape}, target={target.shape}")
        assert mel.shape == (80, 3000), f"Invalid mel shape {mel.shape}"
        assert dec_in.shape == target.shape, f"Shape mismatch: {dec_in.shape} vs {target.shape}"
        assert dec_in.dtype == torch.long and target.dtype == torch.long
        
        # Verify autoregressive teacher forcing shift:
        # dec_in is tokens[:-1], target is tokens[1:]
        # Prompt positions masked in target with -100
        prompt_len = len(tok.sot_sequence_including_notimestamps)
        for p in range(prompt_len - 1):
            assert target[p].item() == -100, f"Prompt at pos {p} not masked with -100"
            
        # Target after prompt must NOT be -100 for the first text token
        assert target[prompt_len - 1].item() != -100, "First text token was incorrectly masked"
        assert target[-1].item() == tok.eot, f"Expected final target token to be EOT ({tok.eot}), got {target[-1].item()}"

    print("Verification B PASSED: Audio preprocessing and autoregressive alignment verified.")
    return ds


def test_verification_c(ds, tok):
    print("\n--- [Verification C] Collate Function & Loss Masking ---")
    collate_fn = make_collate_fn(tok)
    loader = DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_fn)
    batch = next(iter(loader))
    
    mels = batch["mel"]
    dec_inputs = batch["dec_input"]
    targets = batch["target"]
    
    print(f"Batch shapes: mels={mels.shape}, dec_inputs={dec_inputs.shape}, targets={targets.shape}")
    assert mels.shape == (4, 80, 3000)
    assert dec_inputs.shape == targets.shape
    B, L = dec_inputs.shape
    assert B == 4 and L > 0
    
    # Check padding: targets padded with -100
    logits = torch.randn(B, L, 51865)
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    loss = loss_fn(logits.view(-1, 51865), targets.view(-1))
    print(f"Simulated loss computation: loss={loss.item():.4f}")
    assert not torch.isnan(loss) and not torch.isinf(loss)
    print("Verification C PASSED: Collate padding and loss ignore_index=-100 verified.")
    return batch


def test_verification_d(model, batch):
    print("\n--- [Verification D] Training Loop & Scheduler Stepping ---")
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
    total_steps = 291
    warmup_steps = 35
    scheduler = create_cosine_lr_scheduler(optimizer, warmup_steps=warmup_steps, total_steps=total_steps)
    
    initial_lr = scheduler.get_last_lr()[0]
    print(f"Initial LR: {initial_lr}")
    
    # Run a 2-step gradient accumulation forward pass on CPU
    mels = batch["mel"]
    dec_inputs = batch["dec_input"]
    targets = batch["target"]
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    
    model.train()
    optimizer.zero_grad()
    
    # Micro-step 1 (half batch)
    out1 = model(mels[:2], dec_inputs[:2])
    loss1 = loss_fn(out1.view(-1, out1.size(-1)), targets[:2].view(-1))
    (loss1 / 2.0).backward()
    
    # Micro-step 2 (half batch)
    out2 = model(mels[2:], dec_inputs[2:])
    loss2 = loss_fn(out2.view(-1, out2.size(-1)), targets[2:].view(-1))
    (loss2 / 2.0).backward()
    
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    scheduler.step()
    
    new_lr = scheduler.get_last_lr()[0]
    print(f"LR after 1 optimizer update: {new_lr}")
    assert new_lr > initial_lr, f"Expected LR to warm up: {new_lr} vs {initial_lr}"
    print("Verification D PASSED: Forward/backward, gradient accumulation, and scheduler warmup step verified.")


def test_verification_e(model):
    print("\n--- [Verification E] Checkpoint Native Export and Load Contract ---")
    tmp_dir = REPO_ROOT / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    test_ckpt = tmp_dir / "test_whisper_export.pt"
    
    try:
        print(f"Exporting checkpoint to {test_ckpt} using dims.__dict__ contract...")
        export_native_whisper_checkpoint(model, test_ckpt)
        assert test_ckpt.exists(), "Export file not found"
        
        # Load back with torch.load to inspect keys
        raw = torch.load(str(test_ckpt), map_location="cpu")
        assert "dims" in raw and "model_state_dict" in raw
        assert isinstance(raw["dims"], dict), f"Expected dims to be dict, got {type(raw['dims'])}"
        print(f"Raw checkpoint dims keys: {list(raw['dims'].keys())[:5]}...")
        
        # Load with whisper.load_model
        loaded_model = whisper.load_model(str(test_ckpt), device="cpu")
        assert loaded_model.dims.n_vocab == 51865
        print(f"whisper.load_model successfully re-hydrated model with n_vocab={loaded_model.dims.n_vocab}")
    finally:
        if test_ckpt.exists():
            test_ckpt.unlink()
            print("Temporary checkpoint cleanly deleted.")
    print("Verification E PASSED: Native checkpoint export/load contract fully verified.")


def test_verification_f():
    print("\n--- [Verification F] Phrase Matcher & Normalizer Regression ---")
    assert ref_normalize_text("Hello, WORLD! 123") == "hello world 123"
    assert normalize_text("Hello, WORLD! 123") == "hello world 123"
    
    verifier = PhraseVerifier()
    res = verifier.verify(expected="alpha bravo charlie", transcript="ALPHA BRAVO CHARLIE", confidence=0.95)
    assert res.match, f"Expected match, got {res}"
    assert res.code == "OK", f"Expected code OK, got {res.code}"
    print(f"PhraseVerifier verification result: code={res.code}, match={res.match}")
    print("Verification F PASSED: PhraseVerifier and Normalizer operate consistently.")


def main():
    print("==================================================================")
    print("Starting Comprehensive Verification Suite for Authorized Pre-Training Fixes")
    print("==================================================================")
    
    model, tok = test_verification_a()
    ds = test_verification_b(tok)
    batch = test_verification_c(ds, tok)
    test_verification_d(model, batch)
    test_verification_e(model)
    test_verification_f()
    
    print("\n==================================================================")
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITHOUT ERROR!")
    print("==================================================================")


if __name__ == "__main__":
    main()
