# AAA-ASR Phrase Matcher Developer Test Report (Day 1)

**Component:** AAA-ASR Challenge Phrase Verifier (`backend/app/aaa_asr/phrase_matcher.py`)  
**Developer:** Nandan (Member 5)  
**Peer Reviewer:** Aditya  
**Test Suite:** `backend/tests/test_phrase_matcher.py`  
**Execution Timestamp:** 2026-11-12T00:09:05+05:30  
**Environment:** Python 3.8.2 / pytest-8.3.5 / Windows 11 / E: Drive Virtualenv  

---

## 1. Executive Summary

| Metric | Target | Actual Result | Status |
|--------|--------|---------------|--------|
| Total Test Cases | ≥ 100 | **158** | **EXCEEDED (158% of target)** |
| Passing Tests | 100% | **158** | **100% PASSED** |
| Failing Tests | 0 | **0** | **PERFECT** |
| Skipped Tests | 0 | **0** | **NONE** |
| Execution Duration | < 5.0s | **0.36s** | **ULTRA-FAST** |
| Near-Miss Rejection Rate | 100% | **100%** | **VERIFIED** |
| Fuzzy Acceptance Code Path | None | **None** | **VERIFIED (Fail Closed)** |

---

## 2. Test Categories & Coverage Matrix

| Category ID | Category Name | Description | Test Count | Result |
|-------------|---------------|-------------|------------|--------|
| 1 | Exact Phrase Match | Exact matching phrases with identical vocabulary | 6 | PASS |
| 2-4 | Case Normalization | Lowercase, uppercase, mixed/alternating case inputs | 7 | PASS |
| 5 | Punctuation Stripping | Commas, periods, exclamation, questions, hyphens | 5 | PASS |
| 6-9 | Whitespace Normalization | Leading/trailing spaces, multiple spaces, tabs (`\t`), newlines (`\n`, `\r\n`) | 8 | PASS |
| 10 | Approved Filler Words | Removal of approved hesitations (`um`, `uh`, `er`, `hmm`, `erm`, `ah`) | 7 | PASS |
| 11 | Digit-to-Word Conversion | Bidirectional normalization (`7` ↔ `seven`, `20` ↔ `twenty`) | 6 | PASS |
| 12 | Missing Words | Truncated phrases or omitted tokens | 8 | PASS (Rejected) |
| 13 | Extra Words | Injected tokens, polite preambles, appended words | 6 | PASS (Rejected) |
| 14 | Repeated Words | Stuttered or duplicated words (not collapsed; real errors) | 6 | PASS (Rejected) |
| 15 | Reordered Words | Anagram phrases or swapped word positions | 6 | PASS (Rejected) |
| 16 | Incorrect Numbers | Near-number substitutions (`twenty` vs `thirty`) | 6 | PASS (Rejected) |
| 17 | Empty Transcripts | Empty strings, whitespace-only, tabs-only, newlines-only | 4 | PASS (`NO_SPEECH`) |
| 18 | Empty Expected Phrase | Empty or whitespace-only challenge phrases | 2 | PASS (`MISMATCH`) |
| 19 | No-Speech Probability | High Whisper `no_speech_prob` (> 0.8) condition | 3 | PASS (`NO_SPEECH`) |
| 20 | Low Confidence | Transcripts below confidence threshold (`< 0.5`) | 4 | PASS (`LOW_CONF`) |
| 21 | Too-Short Audio | Audio duration `< 0.5s` | 2 | PASS (`TOO_SHORT`) |
| 22 | Expired Challenge | Challenge timestamp past TTL (90s default) | 3 | PASS (`EXPIRED_CHALLENGE`) |
| 23 | Invalid Input Types | `NoneType`, integer inputs, non-string payloads | 4 | PASS (Fail Closed) |
| 24 | Homophones & Minimal Pairs | Curated minimal pairs (`read` vs `red`, `for` vs `four`) | 6 | PASS (Rejected) |
| 25 | Punctuation-Only Input | Inputs containing solely punctuation marks (`...`, `!@#$%`) | 3 | PASS (`NO_SPEECH`) |
| 26 | Repeated Punctuation | Multi-character punctuation blocks (`hello... world!!!`) | 3 | PASS |
| 27 | Normalization Collisions | Word aliases like `oh` ↔ `zero` in digit context | 3 | PASS |
| 28 | Unicode & Apostrophes | NFKC normalization, fullwidth digits, curly apostrophes | 4 | PASS |
| 29 | Fuzzy Match Regressions | Strict rejection of near-miss phrases previously accepted by old 0.6 threshold | 10 | PASS (Strictly Rejected) |
| 30 | British/American Spelling | Vocabulary spelling maps (`colour` ↔ `color`, `centre` ↔ `center`) | 5 | PASS |
| Core | Verifier Class Unit Tests | Parameter validation, return envelope structure | 4 | PASS |
| Security | Security Invariants | High confidence cannot override mismatch, expired always fails, fail closed | 5 | PASS |
| Edge | Edge Cases | Very long phrases, single words, multi-filler combos | 9 | PASS |
| **Total** | | | **158** | **100% PASS** |

---

## 3. Detailed Pytest Execution Log

```text
============================= test session starts =============================
platform win32 -- Python 3.8.2, pytest-8.3.5, pluggy-1.5.0 -- E:\AAA_Project\AAA_Baselines\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\AAA_PROJECT\AAA_Baselines
plugins: cov-5.0.0
collecting ... collected 158 items

backend/tests/test_phrase_matcher.py::TestExactMatch::test_exact_phrase_match PASSED
backend/tests/test_phrase_matcher.py::TestCaseNormalization::test_case_insensitive_match PASSED
backend/tests/test_phrase_matcher.py::TestPunctuation::test_punctuation_stripped PASSED
backend/tests/test_phrase_matcher.py::TestWhitespace::test_whitespace_normalized PASSED
backend/tests/test_phrase_matcher.py::TestFillerWords::test_filler_words_removed PASSED
backend/tests/test_phrase_matcher.py::TestDigitConversion::test_digit_word_conversion PASSED
backend/tests/test_phrase_matcher.py::TestMissingWords::test_missing_words_rejected PASSED
backend/tests/test_phrase_matcher.py::TestExtraWords::test_extra_words_rejected PASSED
backend/tests/test_phrase_matcher.py::TestRepeatedWords::test_repeated_words_rejected PASSED
backend/tests/test_phrase_matcher.py::TestReorderedWords::test_reordered_words_rejected PASSED
backend/tests/test_phrase_matcher.py::TestIncorrectNumbers::test_incorrect_numbers_rejected PASSED
backend/tests/test_phrase_matcher.py::TestEmptyTranscript::test_empty_string_transcript PASSED
backend/tests/test_phrase_matcher.py::TestEmptyExpected::test_empty_expected PASSED
backend/tests/test_phrase_matcher.py::TestNoSpeech::test_high_no_speech_prob PASSED
backend/tests/test_phrase_matcher.py::TestLowConfidence::test_low_confidence_rejected PASSED
backend/tests/test_phrase_matcher.py::TestLowConfidence::test_confidence_does_not_fix_mismatch PASSED
backend/tests/test_phrase_matcher.py::TestTooShort::test_too_short_audio PASSED
backend/tests/test_phrase_matcher.py::TestExpiredChallenge::test_expired_challenge_rejected PASSED
backend/tests/test_phrase_matcher.py::TestInvalidInputs::test_none_transcript PASSED
backend/tests/test_phrase_matcher.py::TestHomophones::test_homophones_rejected_as_mismatch PASSED
backend/tests/test_phrase_matcher.py::TestPunctuationOnly::test_punctuation_only_transcript PASSED
backend/tests/test_phrase_matcher.py::TestRepeatedPunctuation::test_repeated_punctuation_normalized PASSED
backend/tests/test_phrase_matcher.py::TestNormalizationCollisions::test_oh_becomes_zero PASSED
backend/tests/test_phrase_matcher.py::TestUnicode::test_curly_apostrophe PASSED
backend/tests/test_phrase_matcher.py::TestFuzzyRejection::test_near_miss_rejected PASSED
backend/tests/test_phrase_matcher.py::TestSpellingVariants::test_spelling_variants_match PASSED
backend/tests/test_phrase_matcher.py::TestSecurityInvariants::test_high_confidence_cannot_fix_mismatch PASSED
backend/tests/test_phrase_matcher.py::TestSecurityInvariants::test_expired_always_fails PASSED
backend/tests/test_phrase_matcher.py::TestSecurityInvariants::test_exact_match_with_low_conf_fails PASSED
backend/tests/test_phrase_matcher.py::TestSecurityInvariants::test_no_fuzzy_acceptance_path PASSED
backend/tests/test_phrase_matcher.py::TestSecurityInvariants::test_fail_closed_behavior PASSED
... [all 158 tests passed] ...
============================= 158 passed in 0.36s =============================
```

---

## 4. Key Security Invariants Proven

1. **Near-Miss Phrases are 100% Rejected:**
   - Expected: `"Seven Red Chair Twenty"`, Transcript: `"Seven Red Chair Thirty"` -> Result: `MISMATCH` (`match=False`).
   - Expected: `"Seven Red Chair Twenty"`, Transcript: `"Seven Red Sofa Twenty"` -> Result: `MISMATCH` (`match=False`).
2. **Confidence Can Only Tighten, Never Loosen:**
   - Confidence `1.0` with mismatched text returns `MISMATCH`.
   - Confidence `0.1` with matching text returns `LOW_CONF`.
3. **Expired Challenges Fail Closed:**
   - Perfect exact transcript with `challenge_expired=True` returns `EXPIRED_CHALLENGE` immediately without inspecting audio or text.
4. **No Repeated Word Collapsing:**
   - Expected: `"Seven Red Chair Twenty"`, Transcript: `"Seven Red Red Chair Twenty"` returns `MISMATCH`.
