import pytest

from backend.video_detection import aggregate_temporal_detections, normalize_hazard_label


def test_normalizes_supported_hazard_aliases():
    assert normalize_hazard_label("flood_water") == "Flood"
    assert normalize_hazard_label("Smoke") == "Fire / smoke"
    assert normalize_hazard_label("fallen-tree") == "Blocked road"
    assert normalize_hazard_label("person") is None


def test_requires_temporal_confirmation_across_distinct_frames():
    frames = [
        [{"label": "fire", "confidence": 0.8}, {"label": "fire", "confidence": 0.7}],
        [{"label": "smoke", "confidence": 0.9}],
        [{"label": "fire", "confidence": 0.6}],
    ]
    result = aggregate_temporal_detections(frames, min_frames=3)
    assert result["confirmed_hazards"] == ["Fire / smoke"]
    assert result["frame_hits"]["Fire / smoke"] == 3


def test_single_frame_is_not_confirmed_by_default():
    result = aggregate_temporal_detections([[{"label": "flood", "confidence": 0.95}]], min_frames=3)
    assert result["confirmed_hazards"] == []


def test_unknown_model_classes_are_ignored():
    result = aggregate_temporal_detections([[{"label": "car", "confidence": 0.99}]], min_frames=1)
    assert result["frame_hits"] == {}
    assert result["confirmed_hazards"] == []


def test_invalid_min_frames_raises():
    with pytest.raises(ValueError, match="min_frames"):
        aggregate_temporal_detections([], min_frames=0)
