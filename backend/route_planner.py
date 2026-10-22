"""Simple route planning for AstraResQ AI's fictional road network.

This module is for educational simulation only. Distances are schematic units,
not kilometres, and must not be used for real-world emergency navigation.
"""

from __future__ import annotations

import heapq
import math
from urllib.parse import urlparse


def _road_weight(road: dict, nodes: dict) -> float:
    """Return configured weight or schematic Euclidean distance."""
    if road.get("weight") is not None:
        weight = float(road["weight"])
        if weight <= 0:
            raise ValueError(f"Road {road.get('id')} must have positive weight.")
        return weight
    start = nodes[road["from"]]
    end = nodes[road["to"]]
    return math.hypot(
        float(start["x"]) - float(end["x"]),
        float(start["y"]) - float(end["y"]),
    )


def find_route(
    network: dict, origin: str, destination: str, blocked_roads=None
) -> dict | None:
    """Find a shortest path using Dijkstra; return None if no path exists."""
    nodes = {node["id"]: node for node in network.get("nodes", [])}
    roads = network.get("roads", [])
    blocked = set(blocked_roads or [])

    if origin not in nodes:
        raise ValueError(f"Unknown origin node: {origin}")
    if destination not in nodes:
        raise ValueError(f"Unknown destination node: {destination}")
    if origin == destination:
        return {"nodes": [origin], "roads": [], "distance": 0.0}

    adjacency = {node_id: [] for node_id in nodes}
    for road in roads:
        road_id = road.get("id")
        start, end = road.get("from"), road.get("to")
        if start not in nodes or end not in nodes:
            raise ValueError(f"Road {road_id} references an unknown node.")
        if road_id in blocked:
            continue
        weight = _road_weight(road, nodes)
        adjacency[start].append((end, road_id, weight))
        adjacency[end].append((start, road_id, weight))

    distances = {origin: 0.0}
    previous = {}
    queue = [(0.0, origin)]

    while queue:
        distance, current = heapq.heappop(queue)
        if distance > distances.get(current, float("inf")):
            continue
        if current == destination:
            break
        for neighbor, road_id, weight in adjacency[current]:
            candidate = distance + weight
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = (current, road_id)
                heapq.heappush(queue, (candidate, neighbor))

    if destination not in distances:
        return None

    path_nodes = [destination]
    path_roads = []
    current = destination
    while current != origin:
        prior, road_id = previous[current]
        path_roads.append(road_id)
        path_nodes.append(prior)
        current = prior

    return {
        "nodes": list(reversed(path_nodes)),
        "roads": list(reversed(path_roads)),
        "distance": distances[destination],
    }


def find_alternative_route(
    network: dict, origin: str, destination: str, blocked_roads=None
) -> dict | None:
    """Find a different candidate route by rerunning Dijkstra without each
    road from the shortest route, then choose the lowest-distance distinct path.
    """
    blocked = set(blocked_roads or [])
    primary = find_route(network, origin, destination, blocked)
    if primary is None or not primary["roads"]:
        return None

    candidates = []
    for road_id in primary["roads"]:
        candidate = find_route(
            network, origin, destination, blocked | {road_id}
        )
        if candidate and candidate["roads"] != primary["roads"]:
            if candidate["roads"] not in [item["roads"] for item in candidates]:
                candidates.append(candidate)

    return min(candidates, key=lambda item: item["distance"]) if candidates else None


def validate_camera_url(url: str) -> str:
    """Accept only RTSP or HTTP(S) URLs for a user-authorized camera stream."""
    candidate = str(url or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"rtsp", "rtsps", "http", "https"}:
        raise ValueError("Use an RTSP, RTSPS, HTTP, or HTTPS camera stream URL.")
    if not parsed.hostname:
        raise ValueError("The camera URL must include a host name or IP address.")
    return candidate


def capture_camera_frame(url: str):
    """Capture one frame from an explicitly supplied authorized camera URL.

    OpenCV is imported lazily so route planning and tests work without it.
    Returns an RGB numpy array. This function does not save or transmit frames.
    """
    safe_url = validate_camera_url(url)
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError(
            "Camera preview requires OpenCV. Install it with "
            "'python -m pip install opencv-python-headless'."
        ) from error

    capture = cv2.VideoCapture(safe_url)
    try:
        if not capture.isOpened():
            raise RuntimeError(
                "Could not open the camera stream. Check the URL, network, "
                "credentials, and camera permissions."
            )
        success, frame = capture.read()
        if not success or frame is None:
            raise RuntimeError(
                "The camera connected but did not provide a frame."
            )
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    finally:
        capture.release()
