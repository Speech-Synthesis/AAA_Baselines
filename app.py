"""
AAA Engine - Gradio Interface
Adaptive Audio Authentication with Deepfake Detection
"""

import os
import sys
import uuid
import tempfile
from datetime import datetime

import gradio as gr
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.layer1_speaker import enroll_speaker, verify_speaker
from app.layer2_deepfake import detect_spoof
from app.layer3_adaptive import generate_challenge, verify_token, update_voiceprint, get_token_phrase
from app.layer3_asr import verify_phrase

# In-memory storage for demo (replace with DB in production)
users_db = {}
voiceprints_db = {}
challenges_db = {}

# Thresholds
L2_SPOOF_THRESHOLD = 0.5
L1_SIMILARITY_THRESHOLD = 0.50
ASR_PHRASE_THRESHOLD = 0.6


def register_user(name: str, email: str):
    """Register a new user."""
    if not name or not email:
        return "Please provide both name and email.", None

    # Check if email exists
    for uid, user in users_db.items():
        if user['email'] == email:
            return f"Email already registered. User ID: {uid}", uid

    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        'name': name,
        'email': email,
        'created_at': datetime.utcnow()
    }

    return f"Registration successful!\n\nUser ID: {user_id}\n\nSave this ID for enrollment and verification.", user_id


def enroll_voice(user_id: str, audio):
    """Enroll user's voice sample."""
    if not user_id or user_id not in users_db:
        return "Invalid User ID. Please register first."

    if audio is None:
        return "Please record an audio sample."

    # Get audio data
    sample_rate, audio_data = audio

    # Convert to bytes (WAV format)
    import io
    import soundfile as sf

    # Normalize audio
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Save to bytes
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    audio_bytes = buffer.getvalue()

    # Extract embedding
    result = enroll_speaker(audio_bytes)
    embedding = result["embedding"]

    # Update voiceprint
    if user_id in voiceprints_db:
        old_embedding = voiceprints_db[user_id]['embedding']
        new_embedding = update_voiceprint(old_embedding, embedding)
        voiceprints_db[user_id]['embedding'] = new_embedding
        voiceprints_db[user_id]['sample_count'] += 1
    else:
        voiceprints_db[user_id] = {
            'embedding': embedding,
            'sample_count': 1
        }

    count = voiceprints_db[user_id]['sample_count']
    return f"Enrollment successful!\n\nSample count: {count}\n\nRecord more samples for better accuracy (recommended: 3+)."


def get_challenge(user_id: str):
    """Generate authentication challenge."""
    if not user_id or user_id not in users_db:
        return "Invalid User ID.", None, None

    if user_id not in voiceprints_db:
        return "No voiceprint enrolled. Please enroll first.", None, None

    # Generate challenge
    challenge = generate_challenge(user_id)

    # Store challenge
    challenges_db[challenge['token']] = {
        'user_id': user_id,
        'phrase': challenge['phrase'],
        'expires_at': challenge['expires_at'],
        'used': False
    }

    return f"Please speak this phrase:\n\n**{challenge['phrase']}**\n\n(Valid for 90 seconds)", challenge['phrase'], challenge['token']


def verify_voice(user_id: str, token: str, audio):
    """Verify user's voice against challenge."""
    if not user_id or user_id not in users_db:
        return "Invalid User ID."

    if not token or token not in challenges_db:
        return "Invalid or expired token. Please get a new challenge."

    if audio is None:
        return "Please record your response."

    challenge = challenges_db[token]

    if challenge['used']:
        return "Token already used. Please get a new challenge."

    if datetime.utcnow() > challenge['expires_at']:
        return "Token expired. Please get a new challenge."

    # Get voiceprint
    voiceprint = voiceprints_db.get(user_id)
    if not voiceprint:
        return "No voiceprint found."

    # Convert audio to bytes
    sample_rate, audio_data = audio

    import io
    import soundfile as sf

    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    audio_bytes = buffer.getvalue()

    # Layer 2: Deepfake Detection
    l2_result = detect_spoof(audio_bytes)
    l2_label = l2_result["label"]
    l2_confidence = l2_result["confidence"]

    if l2_label == "spoof" and l2_confidence > L2_SPOOF_THRESHOLD:
        challenges_db[token]['used'] = True
        return f"""REJECTED - Deepfake Detected

Layer 2 (Deepfake): FAIL
- Label: {l2_label}
- Confidence: {l2_confidence:.2%}

Synthetic or manipulated audio detected."""

    # ASR: Phrase Verification
    expected_phrase = challenge['phrase']
    asr_match, asr_similarity, asr_transcript = verify_phrase(
        audio_bytes, expected_phrase, ASR_PHRASE_THRESHOLD
    )

    if not asr_match:
        challenges_db[token]['used'] = True
        return f"""REJECTED - Wrong Phrase

Layer 2 (Deepfake): PASS ({l2_label}, {l2_confidence:.2%})
Layer ASR (Phrase): FAIL

Expected: "{expected_phrase}"
Heard: "{asr_transcript}"
Similarity: {asr_similarity:.2%}"""

    # Layer 1: Speaker Verification
    l1_result = verify_speaker(audio_bytes, voiceprint['embedding'])
    l1_score = l1_result["score"]
    new_embedding = l1_result["embedding"]

    if l1_score < L1_SIMILARITY_THRESHOLD:
        challenges_db[token]['used'] = True
        return f"""REJECTED - Speaker Mismatch

Layer 2 (Deepfake): PASS ({l2_label}, {l2_confidence:.2%})
Layer ASR (Phrase): PASS ({asr_similarity:.2%})
Layer 1 (Speaker): FAIL

Speaker Score: {l1_score:.2%} (threshold: {L1_SIMILARITY_THRESHOLD:.0%})

Voice does not match enrolled voiceprint."""

    # Success - Update voiceprint with EMA
    updated_embedding = update_voiceprint(voiceprint['embedding'], new_embedding)
    voiceprints_db[user_id]['embedding'] = updated_embedding
    voiceprints_db[user_id]['sample_count'] += 1
    challenges_db[token]['used'] = True

    return f"""ACCEPTED - Authentication Successful

Layer 2 (Deepfake): PASS
- Label: {l2_label}
- Confidence: {l2_confidence:.2%}

Layer ASR (Phrase): PASS
- Transcript: "{asr_transcript}"
- Similarity: {asr_similarity:.2%}

Layer 1 (Speaker): PASS
- Score: {l1_score:.2%}

Layer 3 (Token): PASS
- Voiceprint updated (sample #{voiceprints_db[user_id]['sample_count']})

Session authenticated successfully."""


# Build Gradio Interface
with gr.Blocks(title="AAA Engine", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # AAA Engine - Adaptive Audio Authentication

    A four-layer voice authentication system with deepfake detection.

    **Pipeline:** Deepfake Detection → Phrase Verification → Speaker Verification → Token Validation
    """)

    # State
    current_user_id = gr.State(None)
    current_token = gr.State(None)

    with gr.Tabs():
        # Tab 1: Registration
        with gr.TabItem("1. Register"):
            gr.Markdown("### Create a new account")
            with gr.Row():
                with gr.Column():
                    reg_name = gr.Textbox(label="Name", placeholder="John Doe")
                    reg_email = gr.Textbox(label="Email", placeholder="john@example.com")
                    reg_btn = gr.Button("Register", variant="primary")
                with gr.Column():
                    reg_output = gr.Textbox(label="Result", lines=5, interactive=False)
                    reg_user_id = gr.Textbox(label="Your User ID (save this!)", interactive=False)

            reg_btn.click(
                register_user,
                inputs=[reg_name, reg_email],
                outputs=[reg_output, reg_user_id]
            )

        # Tab 2: Enrollment
        with gr.TabItem("2. Enroll Voice"):
            gr.Markdown("### Record voice samples to create your voiceprint")
            gr.Markdown("Record at least 3 samples (5+ seconds each) for best accuracy.")
            with gr.Row():
                with gr.Column():
                    enroll_user_id = gr.Textbox(label="User ID", placeholder="Paste your User ID here")
                    enroll_audio = gr.Audio(label="Record Voice Sample", sources=["microphone"])
                    enroll_btn = gr.Button("Enroll Sample", variant="primary")
                with gr.Column():
                    enroll_output = gr.Textbox(label="Result", lines=5, interactive=False)

            enroll_btn.click(
                enroll_voice,
                inputs=[enroll_user_id, enroll_audio],
                outputs=[enroll_output]
            )

        # Tab 3: Verification
        with gr.TabItem("3. Verify"):
            gr.Markdown("### Authenticate with your voice")

            with gr.Row():
                with gr.Column():
                    verify_user_id = gr.Textbox(label="User ID", placeholder="Paste your User ID")
                    challenge_btn = gr.Button("Get Challenge Phrase", variant="secondary")
                    challenge_display = gr.Markdown("*Click 'Get Challenge Phrase' to start*")
                    hidden_token = gr.Textbox(visible=False)

                with gr.Column():
                    verify_audio = gr.Audio(label="Speak the Challenge Phrase", sources=["microphone"])
                    verify_btn = gr.Button("Verify", variant="primary")

            verify_output = gr.Textbox(label="Verification Result", lines=12, interactive=False)

            challenge_btn.click(
                get_challenge,
                inputs=[verify_user_id],
                outputs=[challenge_display, gr.Textbox(visible=False), hidden_token]
            )

            verify_btn.click(
                verify_voice,
                inputs=[verify_user_id, hidden_token, verify_audio],
                outputs=[verify_output]
            )

    gr.Markdown("""
    ---
    **Security Layers:**
    - **L2:** Deepfake detection (Wav2Vec2)
    - **ASR:** Phrase verification (Whisper)
    - **L1:** Speaker verification (ECAPA-TDNN)
    - **L3:** Challenge-response tokens (HMAC-SHA256)

    [GitHub](https://github.com/Speech-Synthesis/AAA_Baselines) | MIT License
    """)

if __name__ == "__main__":
    demo.launch()
