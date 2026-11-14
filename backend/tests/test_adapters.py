"""
AAA Engine Model Adapter Tests
Tests for mock and base adapter functionality.
"""



class TestMockSpeakerAdapter:
    """Tests for MockSpeakerAdapter."""

    def test_create_adapter(self):
        """Should create adapter with defaults."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter()
        assert adapter.is_ready() is True

    def test_get_info(self):
        """Should return model info."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter()
        info = adapter.get_info()

        assert info.name == "Mock Speaker Verification"
        assert info.is_loaded is True

    def test_extract_embedding(self):
        """Should extract embedding from audio."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter(embedding_dim=192)
        result = adapter.extract_embedding(b"fake audio data")

        assert len(result.embedding) == 192

    def test_verify_speaker_match(self):
        """Should verify speaker with configurable score."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter(default_score=0.8)
        result = adapter.verify_speaker(b"audio", [], threshold=0.5)

        assert result.score == 0.8
        assert result.is_match is True

    def test_verify_speaker_no_match(self):
        """Should reject speaker below threshold."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter(default_score=0.3)
        result = adapter.verify_speaker(b"audio", [], threshold=0.5)

        assert result.score == 0.3
        assert result.is_match is False

    def test_set_score(self):
        """Should allow changing score for testing."""
        from app.adapters import MockSpeakerAdapter

        adapter = MockSpeakerAdapter()
        adapter.set_score(0.99)

        result = adapter.verify_speaker(b"audio", [], threshold=0.5)
        assert result.score == 0.99


class TestMockDeepfakeAdapter:
    """Tests for MockDeepfakeAdapter."""

    def test_create_adapter(self):
        """Should create adapter with defaults."""
        from app.adapters import MockDeepfakeAdapter

        adapter = MockDeepfakeAdapter()
        assert adapter.is_ready() is True

    def test_detect_bonafide(self):
        """Should detect bonafide audio."""
        from app.adapters import MockDeepfakeAdapter

        adapter = MockDeepfakeAdapter(default_label="bonafide")
        result = adapter.detect(b"audio")

        assert result.label == "bonafide"
        assert result.is_spoof is False

    def test_detect_spoof(self):
        """Should detect spoof audio."""
        from app.adapters import MockDeepfakeAdapter

        adapter = MockDeepfakeAdapter(default_label="spoof")
        result = adapter.detect(b"audio")

        assert result.label == "spoof"
        assert result.is_spoof is True

    def test_is_spoof_method(self):
        """Should provide quick spoof check."""
        from app.adapters import MockDeepfakeAdapter

        adapter = MockDeepfakeAdapter(default_label="spoof", default_confidence=0.9)
        assert adapter.is_spoof(b"audio", threshold=0.5) is True

        adapter.set_result("bonafide", 0.9)
        assert adapter.is_spoof(b"audio", threshold=0.5) is False


class TestMockASRAdapter:
    """Tests for MockASRAdapter."""

    def test_create_adapter(self):
        """Should create adapter with defaults."""
        from app.adapters import MockASRAdapter

        adapter = MockASRAdapter()
        assert adapter.is_ready() is True

    def test_transcribe(self):
        """Should transcribe audio."""
        from app.adapters import MockASRAdapter

        adapter = MockASRAdapter(default_transcript="hello world")
        result = adapter.transcribe(b"audio")

        assert result.transcript == "hello world"

    def test_verify_phrase_match(self):
        """Should verify matching phrase."""
        from app.adapters import MockASRAdapter

        adapter = MockASRAdapter(default_similarity=0.9)
        result = adapter.verify_phrase(b"audio", "test phrase", threshold=0.6)

        assert result.similarity == 0.9

    def test_set_transcript(self):
        """Should allow changing transcript for testing."""
        from app.adapters import MockASRAdapter

        adapter = MockASRAdapter()
        adapter.set_transcript("custom text")

        result = adapter.transcribe(b"audio")
        assert result.transcript == "custom text"


class TestAdapterInterfaces:
    """Tests for adapter interface contracts."""

    def test_speaker_adapter_interface(self):
        """MockSpeakerAdapter should implement full interface."""
        from app.adapters import MockSpeakerAdapter
        from app.adapters.base import SpeakerVerificationAdapter

        adapter = MockSpeakerAdapter()
        assert isinstance(adapter, SpeakerVerificationAdapter)

    def test_deepfake_adapter_interface(self):
        """MockDeepfakeAdapter should implement full interface."""
        from app.adapters import MockDeepfakeAdapter
        from app.adapters.base import DeepfakeDetectionAdapter

        adapter = MockDeepfakeAdapter()
        assert isinstance(adapter, DeepfakeDetectionAdapter)

    def test_asr_adapter_interface(self):
        """MockASRAdapter should implement full interface."""
        from app.adapters import MockASRAdapter
        from app.adapters.base import ASRAdapter

        adapter = MockASRAdapter()
        assert isinstance(adapter, ASRAdapter)
