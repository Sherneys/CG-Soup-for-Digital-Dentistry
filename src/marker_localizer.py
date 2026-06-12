"""S4 module: back-project 2D marker detections to 3D camera-frame points (Track B).

Combines marker_detector.py output with TrueDepth depth maps and camera
intrinsics (Step B3 in docs/ARCHITECTURE.md):

    X = (u - cx) * depth / fx
    Y = (v - cy) * depth / fy
    Z = depth

Conventions:
  - Depth maps: one float32 .npy per frame, values in METERS (ARKit native),
    NaN/0 = invalid. Named by pattern, e.g. depth_000012.npy.
  - Detections (u, v) are in RGB pixel coordinates. If the RGB stream has a
    different resolution than the depth map (typical for TrueDepth: RGB
    1920x1440 vs depth 640x480), pass --rgb-size so (u, v) get rescaled.
  - Intrinsics must correspond to the DEPTH map resolution.
  - Output points are in MILLIMETERS, camera coordinate frame.

intrinsics.json format:
    {"fx": 590.0, "fy": 590.0, "cx": 320.0, "cy": 240.0, "width": 640, "height": 480}

Usage:
    python marker_localizer.py detections.json intrinsics.json \
        --depth-dir ../data/session01/depth --pattern "depth_{frame:06d}.npy" \
        --rgb-size 1920 1440 --out ../output/points3d.json
"""

import argparse
import json
import os
from dataclasses import dataclass

import numpy as np

M_TO_MM = 1000.0
DEPTH_SAMPLE_WINDOW_PX = 5  # median over a small patch rejects single-pixel noise


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    @classmethod
    def from_json(cls, path: str) -> "CameraIntrinsics":
        with open(path) as fh:
            d = json.load(fh)
        return cls(fx=float(d["fx"]), fy=float(d["fy"]),
                   cx=float(d["cx"]), cy=float(d["cy"]),
                   width=int(d["width"]), height=int(d["height"]))


def sample_depth(depth_m: np.ndarray, u: float, v: float,
                 window: int = DEPTH_SAMPLE_WINDOW_PX) -> float:
    """Median of valid depth values in a (window x window) patch around (u, v).

    Returns NaN when the patch contains no valid (finite, positive) depth.
    """
    h, w = depth_m.shape
    col, row = int(round(u)), int(round(v))
    if not (0 <= col < w and 0 <= row < h):
        return float("nan")
    half = window // 2
    patch = depth_m[max(0, row - half):row + half + 1,
                    max(0, col - half):col + half + 1]
    valid = patch[np.isfinite(patch) & (patch > 0)]
    if valid.size == 0:
        return float("nan")
    return float(np.median(valid))


def back_project(u: float, v: float, depth_m: float,
                 K: CameraIntrinsics) -> np.ndarray:
    """Pinhole back-projection of a depth-map pixel to camera-frame mm."""
    z = depth_m * M_TO_MM
    x = (u - K.cx) * z / K.fx
    y = (v - K.cy) * z / K.fy
    return np.array([x, y, z])


def localize_frame(markers: list[dict], depth_m: np.ndarray, K: CameraIntrinsics,
                   rgb_size: tuple[int, int] | None = None) -> dict[str, np.ndarray]:
    """3D camera-frame point (mm) per marker id; markers without depth are dropped.

    markers: [{"id": str, "u": float, "v": float, ...}, ...] from marker_detector.
    rgb_size: (width, height) of the RGB stream if it differs from the depth map.
    """
    su = sv = 1.0
    if rgb_size is not None:
        su = depth_m.shape[1] / rgb_size[0]
        sv = depth_m.shape[0] / rgb_size[1]

    points: dict[str, np.ndarray] = {}
    for m in markers:
        u, v = m["u"] * su, m["v"] * sv
        z = sample_depth(depth_m, u, v)
        if not np.isfinite(z):
            continue
        points[m["id"]] = back_project(u, v, z, K)
    return points


def localize_all(frames: list[dict], depth_dir: str, pattern: str,
                 K: CameraIntrinsics,
                 rgb_size: tuple[int, int] | None = None) -> list[dict]:
    """Run localize_frame over every detection frame that has a depth map."""
    out = []
    for f in frames:
        depth_path = os.path.join(depth_dir, pattern.format(frame=int(f["frame"])))
        if not os.path.exists(depth_path):
            continue
        depth_m = np.load(depth_path)
        points = localize_frame(f["markers"], depth_m, K, rgb_size)
        out.append({"frame": int(f["frame"]), "t_ms": float(f.get("t_ms", 0.0)),
                    "points": {k: v.tolist() for k, v in points.items()}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("detections", help="detections.json from marker_detector.py")
    ap.add_argument("intrinsics", help="intrinsics.json (depth-map resolution)")
    ap.add_argument("--depth-dir", required=True, help="directory of per-frame .npy depth maps")
    ap.add_argument("--pattern", default="depth_{frame:06d}.npy")
    ap.add_argument("--rgb-size", type=int, nargs=2, metavar=("W", "H"),
                    help="RGB resolution if it differs from the depth map")
    ap.add_argument("--out", default="points3d.json")
    args = ap.parse_args()

    K = CameraIntrinsics.from_json(args.intrinsics)
    with open(args.detections) as fh:
        frames = json.load(fh)["frames"]

    rgb_size = (args.rgb_size[0], args.rgb_size[1]) if args.rgb_size else None
    results = localize_all(frames, args.depth_dir, args.pattern, K, rgb_size)

    n_pts = sum(len(f["points"]) for f in results)
    with open(args.out, "w") as fh:
        json.dump({"units": "mm", "coordinate_frame": "camera", "frames": results}, fh, indent=2)
    print(f"localized {n_pts} marker points over {len(results)}/{len(frames)} frames")
    print("saved:", args.out)


if __name__ == "__main__":
    main()
