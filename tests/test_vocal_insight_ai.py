import pytest
import numpy as np
from vocal_insight_ai import get_segment_boundaries, process_boundaries, analyze_segment_with_praat, generate_llm_prompt, analyze_audio_segments, default_analysis_config

# Mock parselmouth.Sound for analyze_segment_with_praat
class MockSound:
    def __init__(self, y, sr):
        self.y = y
        self.sr = sr

    def to_pitch(self):
        # Simplified mock: returns a Pitch object with some dummy data
        class MockPitch:
            def ts(self):
                return np.array([0.1, 0.2, 0.3])
            selected_array = {'frequency': np.array([100, 110, 0])}
        return MockPitch()

    def to_harmonicity(self):
        # Simplified mock: returns a Harmonicity object with some dummy data
        class MockHarmonicity:
            def get_value(self, time):
                return 15.0 # Dummy HNR value
        return MockHarmonicity()

    def to_formant_burg(self):
        # Simplified mock: returns a Formant object with some dummy data
        class MockFormant:
            def ts(self):
                return np.array([0.1, 0.2, 0.3])
            def get_value_at_time(self, formant_num, time):
                if formant_num == 1: return 500.0
                if formant_num == 2: return 1500.0
                if formant_num == 3: return 2500.0
                return 0.0
        return MockFormant()

@pytest.fixture(autouse=True)
def mock_parselmouth_sound(monkeypatch):
    monkeypatch.setattr('parselmouth.Sound', MockSound)


def test_get_segment_boundaries():
    y = np.random.rand(44100 * 10) # 10 seconds of audio
    sr = 44100
    boundaries = get_segment_boundaries(y, sr, 95)
    assert isinstance(boundaries, np.ndarray)
    assert len(boundaries) >= 0 # Can be empty if no changes

def test_process_boundaries():
    boundaries_sec = np.array([1.0, 3.0, 5.0, 7.0])
    total_duration = 10.0
    min_len = 2.0
    max_len = 4.0
    final_boundaries = process_boundaries(boundaries_sec, total_duration, min_len, max_len)
    assert isinstance(final_boundaries, np.ndarray)
    assert len(final_boundaries) > 0
    assert final_boundaries[0] == 0.0
    assert final_boundaries[-1] == total_duration

def test_analyze_segment_with_praat():
    y_segment = np.random.rand(44100 * 2) # 2 seconds of audio
    sr = 44100
    features = analyze_segment_with_praat(y_segment, sr)
    assert isinstance(features, dict)
    assert "f0_mean_hz" in features
    assert "hnr_mean_db" in features

def test_generate_llm_prompt():
    analysis_data = [
        {"segment_id": 1, "time_start_s": 0.0, "time_end_s": 5.0, "features": {"f0_mean_hz": 150, "f0_std_hz": 5, "hnr_mean_db": 10, "f1_mean_hz": 500, "f2_mean_hz": 1500, "f3_mean_hz": 2500}},
        {"segment_id": 2, "time_start_s": 5.0, "time_end_s": 10.0, "features": {"f0_mean_hz": 200, "f0_std_hz": 10, "hnr_mean_db": 12, "f1_mean_hz": 550, "f2_mean_hz": 1600, "f3_mean_hz": 2600}},
    ]
    filename = "test_song.wav"
    prompt = generate_llm_prompt(analysis_data, filename)
    assert isinstance(prompt, str)
    assert "test_song.wav" in prompt
    assert "Segment 1" in prompt

def test_analyze_audio_segments():
    y = np.random.rand(44100 * 15) # 15 seconds of audio
    sr = 44100
    filename = "test_audio.wav"
    
    results, prompt = analyze_audio_segments(y, sr, filename, config=default_analysis_config)
    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(prompt, str)
    assert "test_audio.wav" in prompt
