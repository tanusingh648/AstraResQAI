import pytest

from backend.route_planner import (
    find_route,
    find_alternative_route,
    validate_camera_url,
)


@pytest.fixture
def network():
    return {
        "nodes": [
            {"id": "A", "name": "Start", "x": 0, "y": 0},
            {"id": "B", "name": "Middle", "x": 1, "y": 0},
            {"id": "C", "name": "End", "x": 2, "y": 0},
            {"id": "D", "name": "Detour", "x": 1, "y": 1},
        ],
        "roads": [
            {"id": "AB", "from": "A", "to": "B"},
            {"id": "BC", "from": "B", "to": "C"},
            {"id": "AD", "from": "A", "to": "D"},
            {"id": "DC", "from": "D", "to": "C"},
        ],
    }


def test_finds_shortest_route(network):
    result = find_route(network, "A", "C")
    assert result["nodes"] == ["A", "B", "C"]
    assert result["roads"] == ["AB", "BC"]
    assert result["distance"] == pytest.approx(2.0)


def test_blocked_road_is_avoided(network):
    result = find_route(network, "A", "C", blocked_roads={"AB"})
    assert result["roads"] == ["AD", "DC"]
    assert "AB" not in result["roads"]


def test_alternative_route_is_distinct(network):
    primary = find_route(network, "A", "C")
    alternative = find_alternative_route(network, "A", "C")
    assert alternative is not None
    assert alternative["roads"] != primary["roads"]


def test_returns_none_when_all_routes_blocked(network):
    result = find_route(network, "A", "C", blocked_roads={"AB", "BC", "AD", "DC"})
    assert result is None


def test_unknown_node_raises_helpful_error(network):
    with pytest.raises(ValueError, match="Unknown origin"):
        find_route(network, "MISSING", "C")


@pytest.mark.parametrize("url", [
    "rtsp://camera.local/live",
    "rtsps://camera.local/live",
    "http://192.168.1.10:8080/video",
    "https://camera.example/stream",
])
def test_accepts_supported_camera_protocols(url):
    assert validate_camera_url(url) == url


@pytest.mark.parametrize("url", ["", "camera.local/live", "ftp://camera.local/video", "rtsp://"])
def test_rejects_invalid_camera_urls(url):
    with pytest.raises(ValueError):
        validate_camera_url(url)
