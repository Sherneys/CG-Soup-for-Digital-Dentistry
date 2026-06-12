"""S5 module: rigid registration of labeled landmark sets into the dental frame.

Solves T (4x4) such that  dst ~= T @ src  from two labeled point sets (mm),
e.g. marker positions seen in the camera frame vs the same markers in the
intraoral scan (dental frame). The same tool registers the Track A face
model into the dental frame via shared landmarks from the "smile showing
teeth" bridge set (Step C1 in docs/ARCHITECTURE.md).

Point file format (flat, labels must match between the two files):
    {"P1": [x, y, z], "P2": [x, y, z], ...}

Optionally applies the solved transform to a mesh (OBJ/STL/PLY via trimesh).

Usage:
    python registration.py src_points.json dst_points.json \
        --out ../output/transform.json \
        [--apply-mesh face_model.obj --mesh-out face_model_dental.obj] \
        [--src-frame camera --dst-frame dental]
"""

import argparse
import json

import numpy as np

from jaw_tracker import MIN_MARKERS_PER_ARCH, rigid_transform_svd, to_homogeneous


def register_points(src: dict[str, np.ndarray],
                    dst: dict[str, np.ndarray]) -> tuple[np.ndarray, float, int]:
    """Rigid T (4x4) mapping src -> dst from common labels; returns (T, rmse, n)."""
    keys = sorted(set(src) & set(dst))
    if len(keys) < MIN_MARKERS_PER_ARCH:
        raise ValueError(
            f"need >= {MIN_MARKERS_PER_ARCH} common labels, got {len(keys)}: {keys}")
    src_pts = np.array([src[k] for k in keys], dtype=float)
    dst_pts = np.array([dst[k] for k in keys], dtype=float)
    R, t, rmse = rigid_transform_svd(src_pts, dst_pts)
    return to_homogeneous(R, t), rmse, len(keys)


def apply_transform(T: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Apply a 4x4 rigid transform to (N, 3) points."""
    points = np.asarray(points, dtype=float)
    return points @ T[:3, :3].T + T[:3, 3]


def load_points(path: str) -> dict[str, np.ndarray]:
    with open(path) as fh:
        return {k: np.asarray(v, dtype=float) for k, v in json.load(fh).items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src_points", help="labeled points JSON (frame to map FROM)")
    ap.add_argument("dst_points", help="labeled points JSON (frame to map TO)")
    ap.add_argument("--out", default="transform.json")
    ap.add_argument("--src-frame", default="camera")
    ap.add_argument("--dst-frame", default="dental")
    ap.add_argument("--apply-mesh", help="optional mesh to transform into the dst frame")
    ap.add_argument("--mesh-out", help="output path for the transformed mesh")
    args = ap.parse_args()

    src = load_points(args.src_points)
    dst = load_points(args.dst_points)
    T, rmse, n = register_points(src, dst)

    payload = {"T": T.tolist(), "rmse_mm": rmse, "n_landmarks": n,
               "src_frame": args.src_frame, "dst_frame": args.dst_frame}
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"registered {n} landmarks, RMSE = {rmse:.4f} mm")
    print("saved:", args.out)

    if args.apply_mesh:
        if not args.mesh_out:
            raise SystemExit("--apply-mesh requires --mesh-out")
        import trimesh  # heavyweight; only needed for the mesh path
        mesh = trimesh.load(args.apply_mesh, process=False, force="mesh")
        mesh.vertices = apply_transform(T, mesh.vertices.view(np.ndarray))
        mesh.export(args.mesh_out)
        print("saved:", args.mesh_out)


if __name__ == "__main__":
    main()
