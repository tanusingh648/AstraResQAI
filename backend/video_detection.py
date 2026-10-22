"""Video-first hazard detection helpers for the AstraResQ AI simulation.

The detector is intentionally model-agnostic. A local model must actually be
trained with flood, fire/smoke, and/or blocked-road classes to detect them.
This module never changes route closures automatically.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

HAZARD_ALIASES = {
    "flood": "Flood",
    "floodwater": "Flood",
    "flood water": "Flood",
    "waterlogging": "Flood",
    "fire": "Fire / smoke",
    "smoke": "Fire / smoke",
    "fire smoke": "Fire / smoke",
    "flame": "Fire / smoke",
    "blocked road": "Blocked road",
    "road blockage": "Blocked road",
    "roadblock": "Blocked road",
    "obstacle": "Blocked road",
    "debris": "Blocked road",
    "fallen tree": "Blocked road",
}


def normalize_hazard_label(label: str) -> str | None:
    """Map model class labels to supported hazards; unknown labels are ignored."""
    normalized = " ".join(str(label).lower().replace("_", " ").replace("-", " ").split())
    return HAZARD_ALIASES.get(normalized)


def aggregate_temporal_detections(frame_detections: list[list[dict]], min_frames: int = 3) -> dict:
    """Confirm a hazard only when its class appears in enough sampled frames."""
    if min_frames < 1:
        raise ValueError("min_frames must be at least 1")
    counts: Counter[str] = Counter()
    max_confidence: dict[str, float] = {}
    for detections in frame_detections:
        seen_this_frame: set[str] = set()
        for detection in detections:
            hazard = normalize_hazard_label(detection.get("label", ""))
            confidence = float(detection.get("confidence", 0.0))
            if hazard is None or confidence < 0 or confidence > 1:
                continue
            if hazard not in seen_this_frame:
                counts[hazard] += 1
                seen_this_frame.add(hazard)
            max_confidence[hazard] = max(max_confidence.get(hazard, 0.0), confidence)
    return {
        "frame_hits": dict(counts),
        "confirmed_hazards": [hazard for hazard, count in counts.items() if count >= min_frames],
        "max_confidence": max_confidence,
        "min_frames_required": min_frames,
    }


def analyze_video(
    video_path: str | Path,
    detector,
    frame_stride: int = 5,
    min_confirm_frames: int = 3,
    confidence_threshold: float = 0.40,
    max_sampled_frames: int = 600,
) -> dict:
    """Process sampled frames throughout a video using a supplied local detector.

    detector(frame_bgr) must return dictionaries with label, confidence and an
    optional xyxy=[x1,y1,x2,y2] box. OpenCV is imported lazily for testability.
    """
    if frame_stride < 1 or min_confirm_frames < 1 or max_sampled_frames < 1:
        raise ValueError("frame_stride, min_confirm_frames, and max_sampled_frames must be positive")
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("Video detection requires OpenCV. Install requirements-video.txt.") from error

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture.release()
        raise RuntimeError("Could not open this video. Try MP4 (H.264) or another supported video format.")

    detections_by_frame: list[list[dict]] = []
    sampled = 0
    read_index = 0
    last_frame_rgb = None
    try:
        while sampled < max_sampled_frames:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            current_index = read_index
            read_index += 1
            if current_index % frame_stride:
                continue
            raw_detections = detector(frame) or []
            frame_hits = []
            for item in raw_detections:
                confidence = float(item.get("confidence", 0.0))
                label = str(item.get("label", ""))
                hazard = normalize_hazard_label(label)
                if hazard is None or confidence < confidence_threshold:
                    continue
                normalized = {**item, "label": hazard, "confidence": confidence}
                frame_hits.append(normalized)
                box = item.get("xyxy")
                if box and len(box) == 4:
                    x1, y1, x2, y2 = [int(value) for value in box]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 170), 2)
                    cv2.putText(frame, f"{hazard} {confidence:.2f}", (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 170), 2)
            detections_by_frame.append(frame_hits)
            last_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            sampled += 1
    finally:
        capture.release()

    if sampled == 0:
        raise RuntimeError("No frames could be read from the video.")
    summary = aggregate_temporal_detections(detections_by_frame, min_confirm_frames)
    summary.update({
        "frames_read": read_index,
        "frames_sampled": sampled,
        "frame_stride": frame_stride,
        "last_annotated_frame_rgb": last_frame_rgb,
    })
    return summary
