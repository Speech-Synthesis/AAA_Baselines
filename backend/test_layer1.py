"""
Test script for Layer 1 — Speaker Verification
Run: python test_layer1.py

Requires two WAV files in backend/test_audio/:
  - speaker1_enroll.wav  (Speaker A enrollment)
  - speaker1_verify.wav  (Speaker A verification - should match)
  - speaker2.wav         (Speaker B - should NOT match)

You can record these using any tool (Audacity, phone, etc.)
Specs: WAV, 16kHz, mono, 3+ seconds
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.layer1_speaker import enroll_speaker, verify_speaker


def load_wav(filepath: str) -> bytes:
    """Load WAV file as bytes."""
    with open(filepath, "rb") as f:
        return f.read()


def main():
    test_dir = os.path.join(os.path.dirname(__file__), "test_audio")

    # Check if test directory exists
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"Created {test_dir}/")
        print("\nPlease add test WAV files:")
        print("  - speaker1_enroll.wav  (Speaker A enrollment, 3+ seconds)")
        print("  - speaker1_verify.wav  (Speaker A verification)")
        print("  - speaker2.wav         (Speaker B, different person)")
        print("\nSpecs: WAV, 16kHz recommended, mono, 3+ seconds")
        return

    # Define file paths
    enroll_file = os.path.join(test_dir, "speaker1_enroll.wav")
    verify_same_file = os.path.join(test_dir, "speaker1_verify.wav")
    verify_diff_file = os.path.join(test_dir, "speaker2.wav")

    # Check files exist
    missing = []
    for f in [enroll_file, verify_same_file, verify_diff_file]:
        if not os.path.exists(f):
            missing.append(os.path.basename(f))

    if missing:
        print(f"Missing test files in {test_dir}/:")
        for f in missing:
            print(f"  - {f}")
        print("\nPlease add these WAV files and run again.")
        return

    print("=" * 60)
    print("Layer 1 Speaker Verification Test")
    print("=" * 60)

    # Step 1: Enroll Speaker 1
    print("\n[1] Enrolling Speaker 1...")
    enroll_audio = load_wav(enroll_file)
    enroll_result = enroll_speaker(enroll_audio)
    stored_embedding = enroll_result["embedding"]
    print(f"    Embedding extracted: {len(stored_embedding)} dimensions")
    print(f"    First 5 values: {stored_embedding[:5]}")

    # Step 2: Verify with same speaker (should be HIGH score)
    print("\n[2] Verifying with SAME speaker (speaker1_verify.wav)...")
    verify_same_audio = load_wav(verify_same_file)
    result_same = verify_speaker(verify_same_audio, stored_embedding)
    score_same = result_same["score"]
    print(f"    Similarity score: {score_same:.4f}")
    print(f"    Expected: > 0.6 (same speaker)")
    if score_same > 0.6:
        print("    PASS: Same speaker detected correctly")
    else:
        print("    WARNING: Score lower than expected for same speaker")

    # Step 3: Verify with different speaker (should be LOW score)
    print("\n[3] Verifying with DIFFERENT speaker (speaker2.wav)...")
    verify_diff_audio = load_wav(verify_diff_file)
    result_diff = verify_speaker(verify_diff_audio, stored_embedding)
    score_diff = result_diff["score"]
    print(f"    Similarity score: {score_diff:.4f}")
    print(f"    Expected: < 0.6 (different speaker)")
    if score_diff < 0.6:
        print("    PASS: Different speaker rejected correctly")
    else:
        print("    WARNING: Score higher than expected for different speaker")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Same speaker score:      {score_same:.4f}")
    print(f"Different speaker score: {score_diff:.4f}")
    print(f"Score difference:        {score_same - score_diff:.4f}")

    if score_same > 0.6 and score_diff < 0.6:
        print("\nRESULT: Speaker verification working correctly!")
    elif score_same > score_diff:
        print("\nRESULT: Partial success - same speaker scores higher")
        print("        Consider adjusting threshold or getting cleaner audio")
    else:
        print("\nRESULT: Check audio quality - unexpected scores")


if __name__ == "__main__":
    main()
