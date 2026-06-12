"""S5 module: SVD-based rigid-body 6DOF jaw tracking (Track B).

Inputs are labeled 3D marker positions, all in millimeters:
  - dental_markers.json: static marker positions from the intraoral scan,
    taken WITH markers attached (Marker Protocol). Dental coordinate frame.
  - points3d.json: per-frame marker positions from the TrueDepth localizer
    (camera coordinate frame, see marker_localizer.py).

For each frame we solve the rigid transform dental -> camera per arch via
Kabsch/SVD, then express the lower arch relative to the upper:

    T_jaw(t) = inv(T_cam<-upper(t)) @ T_cam<-lower(t)

At the bite (scan) pose T_jaw == identity; deviations are jaw motion in the
dental coordinate frame. The upper arch is assumed rigid with the skull.

dental_markers.json format:
    {"upper": {"U1": [x, y, z], ...}, "lower": {"L1": [x, y, z], ...}}

Usage:
    python jaw_tracker.py dental_markers.json points3d.json \
        --out ../output/jaw_motion.json [--auto-label]
"""

import argparse
import itertools
import json
from dataclasses import dataclass

import numpy as np

MIN_MARKERS_PER_ARCH = 3
MAX_AUTO_LABEL_MARKERS = 8  # brute-force matching is factorial in n


def rigid_transform_svd(src: np.ndarray, dst: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Least-squares R, t with dst ~= R @ src + t, plus RMSE (reflection-safe).

    src, dst: (N, 3) corresponding points, N >= 3.
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 3:
        raise ValueError(f"need matching (N,3) arrays, got {src.shape} and {dst.shape}")
    if src.shape[0] < MIN_MARKERS_PER_ARCH:
        raise ValueError(f"need >= {MIN_MARKERS_PER_ARCH} correspondences, got {src.shape[0]}")

    src_c = src.mean(axis=0)
    dst_c = dst.mean(axis=0)
    H = (src - src_c).T @ (dst - dst_c)
    U, _, Vt = np.linalg.svd(H)
    # guard against reflections (det = -1) from noisy/near-planar configurations
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    t = dst_c - R @ src_c

    residual = (src @ R.T + t) - dst
    rmse = float(np.sqrt(np.mean(np.sum(residual**2, axis=1))))
    return R, t, rmse


def to_homogeneous(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def invert(T: np.ndarray) -> np.ndarray:
    R, t = T[:3, :3], T[:3, 3]
    return to_homogeneous(R.T, -R.T @ t)


@dataclass(frozen=True)
class FramePose:
    """Rigid pose of one arch in one frame: maps dental frame -> camera frame."""
    T: np.ndarray  # (4, 4)
    rmse_mm: float
    n_markers: int


def solve_arch_pose(template: dict[str, np.ndarray],
                    observed: dict[str, np.ndarray]) -> FramePose | None:
    """Pose from labeled correspondences (common keys); None if < 3 in common."""
    keys = sorted(set(template) & set(observed))
    if len(keys) < MIN_MARKERS_PER_ARCH:
        return None
    src = np.array([template[k] for k in keys], dtype=float)
    dst = np.array([observed[k] for k in keys], dtype=float)
    R, t, rmse = rigid_transform_svd(src, dst)
    return FramePose(T=to_homogeneous(R, t), rmse_mm=rmse, n_markers=len(keys))


def match_by_geometry(template: dict[str, np.ndarray],
                      observed: dict[str, np.ndarray]) -> dict[str, str]:
    """Map observed ids -> template labels by inter-marker distance consistency.

    Works because the intraoral scan gives absolute scale: the pairwise
    distance pattern identifies each marker regardless of pose. Brute force
    over permutations; fine for the handful of dots used per arch.
    """
    t_keys = sorted(template)
    o_keys = sorted(observed)
    n = min(len(t_keys), len(o_keys))
    if n < MIN_MARKERS_PER_ARCH:
        raise ValueError(f"need >= {MIN_MARKERS_PER_ARCH} markers on both sides, got {n}")
    if max(len(t_keys), len(o_keys)) > MAX_AUTO_LABEL_MARKERS:
        raise ValueError(f"too many markers for brute-force matching (> {MAX_AUTO_LABEL_MARKERS})")

    t_pts = np.array([template[k] for k in t_keys])
    o_pts = np.array([observed[k] for k in o_keys])
    t_dist = np.linalg.norm(t_pts[:, None] - t_pts[None, :], axis=-1)
    o_dist = np.linalg.norm(o_pts[:, None] - o_pts[None, :], axis=-1)

    best_cost = np.inf
    best: dict[str, str] = {}
    for t_subset in itertools.combinations(range(len(t_keys)), n):
        for o_subset in itertools.permutations(range(len(o_keys)), n):
            sub_t = t_dist[np.ix_(t_subset, t_subset)]
            sub_o = o_dist[np.ix_(o_subset, o_subset)]
            cost = float(np.abs(sub_t - sub_o).sum())
            if cost < best_cost:
                best_cost = cost
                best = {o_keys[o]: t_keys[t] for o, t in zip(o_subset, t_subset)}
    return best


@dataclass(frozen=True)
class JawFrame:
    frame: int
    t_ms: float
    T_jaw: np.ndarray  # (4, 4) lower-arch pose in the (upper-anchored) dental frame
    upper: FramePose
    lower: FramePose


def track_jaw(dental: dict[str, dict[str, np.ndarray]],
              frames: list[dict]) -> list[JawFrame]:
    """Per-frame 6DOF jaw pose from labeled camera-frame marker points.

    dental: {"upper": {label: xyz_mm}, "lower": {label: xyz_mm}}
    frames: [{"frame": int, "t_ms": float, "points": {label: xyz_mm}}, ...]
    Frames where either arch has < 3 visible markers are skipped.
    """
    results = []
    for f in frames:
        points = {k: np.asarray(v, dtype=float) for k, v in f["points"].items()}
        upper = solve_arch_pose(dental["upper"], points)
        lower = solve_arch_pose(dental["lower"], points)
        if upper is None or lower is None:
            continue
        T_jaw = invert(upper.T) @ lower.T
        results.append(JawFrame(frame=int(f["frame"]), t_ms=float(f.get("t_ms", 0.0)),
                                T_jaw=T_jaw, upper=upper, lower=lower))
    return results


def load_labeled_points(path: str) -> dict[str, dict[str, np.ndarray]]:
    with open(path) as fh:
        raw = json.load(fh)
    return {arch: {k: np.asarray(v, dtype=float) for k, v in pts.items()}
            for arch, pts in raw.items()}


def relabel_frames(dental: dict[str, dict[str, np.ndarray]],
                   frames: list[dict]) -> list[dict]:
    """Rename tracker ids ("upper_0", ...) to dental labels via geometry.

    The mapping is solved once on the first frame where both arches have
    enough markers, then applied everywhere (tracker ids are stable).
    """
    mapping: dict[str, str] = {}
    for f in frames:
        points = {k: np.asarray(v, dtype=float) for k, v in f["points"].items()}
        try:
            for arch in ("upper", "lower"):
                obs = {k: v for k, v in points.items() if k.startswith(arch)}
                mapping.update(match_by_geometry(dental[arch], obs))
        except ValueError:
            mapping.clear()
            continue
        break
    if not mapping:
        raise ValueError("no frame has >= 3 visible markers per arch for auto-labeling")
    return [{**f, "points": {mapping[k]: v for k, v in f["points"].items() if k in mapping}}
            for f in frames]


def save_motion(jaw_frames: list[JawFrame], path: str) -> None:
    payload = {
        "coordinate_frame": "dental",
        "units": "mm",
        "frames": [
            {
                "frame": jf.frame,
                "t_ms": jf.t_ms,
                "T": jf.T_jaw.tolist(),
                "rmse_mm": {"upper": jf.upper.rmse_mm, "lower": jf.lower.rmse_mm},
                "n_markers": {"upper": jf.upper.n_markers, "lower": jf.lower.n_markers},
            }
            for jf in jaw_frames
        ],
    }
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dental_markers", help="dental_markers.json (mm, dental frame)")
    ap.add_argument("points3d", help="points3d.json from marker_localizer.py")
    ap.add_argument("--out", default="jaw_motion.json")
    ap.add_argument("--auto-label", action="store_true",
                    help="match tracker ids to dental labels by inter-marker distances")
    args = ap.parse_args()

    dental = load_labeled_points(args.dental_markers)
    with open(args.points3d) as fh:
        frames = json.load(fh)["frames"]
    if args.auto_label:
        frames = relabel_frames(dental, frames)

    jaw_frames = track_jaw(dental, frames)
    if not jaw_frames:
        raise SystemExit("no frame had >= 3 visible markers on both arches")

    save_motion(jaw_frames, args.out)
    rmse_all = [max(jf.upper.rmse_mm, jf.lower.rmse_mm) for jf in jaw_frames]
    print(f"tracked {len(jaw_frames)}/{len(frames)} frames")
    print(f"fit RMSE (mm): median={np.median(rmse_all):.4f} max={np.max(rmse_all):.4f}")
    print("saved:", args.out)


if __name__ == "__main__":
    main()
