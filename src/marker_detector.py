"""S4 module: detect fiducial dot markers in RGB frames (Track B, Step B3).

Color-coded dots distinguish the arches (default: BLUE dots on the upper
teeth, GREEN dots on the lower teeth — adjust HSV ranges per clinic session
lighting via --config). Per arch: HSV threshold -> morphological open ->
contours -> circularity filter -> sub-pixel centroid via image moments.

A nearest-neighbor tracker assigns stable ids ("upper_0", "lower_2", ...)
across frames so downstream modules can follow each physical dot. Mapping
those tracker ids to intraoral-scan labels is done geometrically later
(jaw_tracker.py --auto-label).

Output detections.json:
    {"frames": [{"frame": 0, "t_ms": 33.3,
                 "markers": [{"id": "upper_0", "arch": "upper",
                              "u": 312.4, "v": 208.1,
                              "radius_px": 6.2, "score": 0.91}]}]}

Usage:
    python marker_detector.py video.mp4 --out detections.json [--config cfg.json]
    python marker_detector.py frames_dir/ --fps 30 --out detections.json
"""

import argparse
import glob
import json
import math
import os
from dataclasses import dataclass, field

import cv2
import numpy as np

DEFAULT_ARCH_COLORS = {
    # OpenCV HSV: H in [0, 180)
    "upper": {"hsv_lo": (100, 120, 70), "hsv_hi": (130, 255, 255)},  # blue dots
    "lower": {"hsv_lo": (45, 120, 70), "hsv_hi": (75, 255, 255)},    # green dots
}


@dataclass(frozen=True)
class DetectorConfig:
    arches: dict = field(default_factory=lambda: dict(DEFAULT_ARCH_COLORS))
    min_radius_px: float = 2.0
    max_radius_px: float = 40.0
    min_circularity: float = 0.6
    max_track_jump_px: float = 60.0

    @classmethod
    def from_json(cls, path: str) -> "DetectorConfig":
        with open(path) as fh:
            d = json.load(fh)
        return cls(**d)


@dataclass(frozen=True)
class Detection:
    arch: str
    u: float
    v: float
    radius_px: float
    score: float  # circularity in [0, 1]


def detect_arch(bgr: np.ndarray, arch: str, hsv_lo: tuple, hsv_hi: tuple,
                config: DetectorConfig) -> list[Detection]:
    """Detect circular color blobs of one arch's color in a BGR frame."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_lo), np.array(hsv_hi))
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections = []
    min_area = math.pi * config.min_radius_px**2
    for c in contours:
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, closed=True)
        if area < min_area or perimeter <= 0:
            continue
        circularity = 4 * math.pi * area / perimeter**2
        if circularity < config.min_circularity:
            continue
        (_, _), radius = cv2.minEnclosingCircle(c)
        if radius > config.max_radius_px:
            continue
        m = cv2.moments(c)
        if m["m00"] == 0:
            continue
        detections.append(Detection(arch=arch,
                                    u=m["m10"] / m["m00"], v=m["m01"] / m["m00"],
                                    radius_px=float(radius),
                                    score=float(min(circularity, 1.0))))
    return detections


def detect_in_frame(bgr: np.ndarray, config: DetectorConfig) -> list[Detection]:
    """All arch detections in one frame (unlabeled — no stable ids yet)."""
    out: list[Detection] = []
    for arch, ranges in config.arches.items():
        out.extend(detect_arch(bgr, arch, tuple(ranges["hsv_lo"]),
                               tuple(ranges["hsv_hi"]), config))
    return out


class MarkerTracker:
    """Assign stable per-arch ids across frames by greedy nearest neighbor.

    A detection within max_jump_px of a previously tracked dot inherits its
    id; otherwise it starts a new id. Dots that vanish keep their last
    position so they re-attach after short occlusions.
    """

    def __init__(self, max_jump_px: float):
        self._max_jump = max_jump_px
        self._last: dict[str, tuple[float, float]] = {}
        self._counts: dict[str, int] = {}

    def update(self, detections: list[Detection]) -> list[tuple[str, Detection]]:
        candidates = []
        for i, det in enumerate(detections):
            for known_id, (lu, lv) in self._last.items():
                if not known_id.startswith(det.arch):
                    continue
                dist = math.hypot(det.u - lu, det.v - lv)
                if dist <= self._max_jump:
                    candidates.append((dist, i, known_id))

        assigned: dict[int, str] = {}
        used_ids: set[str] = set()
        for dist, i, known_id in sorted(candidates):
            if i in assigned or known_id in used_ids:
                continue
            assigned[i] = known_id
            used_ids.add(known_id)

        labeled = []
        for i, det in enumerate(detections):
            if i in assigned:
                marker_id = assigned[i]
            else:
                n = self._counts.get(det.arch, 0)
                self._counts[det.arch] = n + 1
                marker_id = f"{det.arch}_{n}"
            self._last[marker_id] = (det.u, det.v)
            labeled.append((marker_id, det))
        return labeled


def iter_frames(source: str, fps: float):
    """Yield (frame_index, t_ms, bgr) from a video file or an image directory."""
    if os.path.isdir(source):
        paths = sorted(p for ext in ("png", "jpg", "jpeg")
                       for p in glob.glob(os.path.join(source, f"*.{ext}")))
        for i, p in enumerate(paths):
            yield i, i * 1000.0 / fps, cv2.imread(p)
        return
    cap = cv2.VideoCapture(source)
    try:
        i = 0
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            t_ms = cap.get(cv2.CAP_PROP_POS_MSEC) or i * 1000.0 / fps
            yield i, t_ms, bgr
            i += 1
    finally:
        cap.release()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="video file (mp4/mov) or directory of frames")
    ap.add_argument("--config", help="detector config JSON (HSV ranges etc.)")
    ap.add_argument("--fps", type=float, default=30.0,
                    help="frame rate used for timestamps when reading image dirs")
    ap.add_argument("--out", default="detections.json")
    args = ap.parse_args()

    config = DetectorConfig.from_json(args.config) if args.config else DetectorConfig()
    tracker = MarkerTracker(config.max_track_jump_px)

    frames = []
    for i, t_ms, bgr in iter_frames(args.source, args.fps):
        if bgr is None:
            continue
        labeled = tracker.update(detect_in_frame(bgr, config))
        frames.append({
            "frame": i,
            "t_ms": t_ms,
            "markers": [
                {"id": marker_id, "arch": d.arch, "u": d.u, "v": d.v,
                 "radius_px": d.radius_px, "score": d.score}
                for marker_id, d in labeled
            ],
        })

    n_det = sum(len(f["markers"]) for f in frames)
    with open(args.out, "w") as fh:
        json.dump({"frames": frames}, fh, indent=2)
    print(f"detected {n_det} markers over {len(frames)} frames")
    print("saved:", args.out)


if __name__ == "__main__":
    main()
