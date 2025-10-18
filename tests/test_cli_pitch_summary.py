"""vocal_insight_cli のピッチ要約整形テスト"""

from __future__ import annotations

from vocal_insight_cli import _append_pitch_summary


def test_append_pitch_summary_includes_section_accuracy() -> None:
    base_prompt = "Line1"
    payload = {
        "mean_cent_deviation": 12.3,
        "hit_rate": 0.8,
        "stability": 0.9,
        "per_section": [
        {
            "section_id": "section_1",
            "start_s": 0.0,
            "end_s": 30.0,
            "mean_cent_deviation": 11.0,
            "hit_rate": 0.82,
        },
        {
            "section_id": "section_2",
            "start_s": 30.0,
            "end_s": 60.0,
            "mean_cent_deviation": 14.5,
            "hit_rate": 0.75,
        },
        ],
    }

    summary = _append_pitch_summary(base_prompt, payload)

    assert "--- Pitch Accuracy ---" in summary
    assert "Mean deviation: 12.3 cent" in summary
    assert "Hit rate: 0.80" in summary
    assert "Stability: 0.90" in summary
    assert "section_1" in summary
    assert "0.0-30.0s" in summary
    assert "hit 0.82" in summary
    assert "deviation 11.0 cent" in summary
    assert "section_2" in summary
    assert "30.0-60.0s" in summary
