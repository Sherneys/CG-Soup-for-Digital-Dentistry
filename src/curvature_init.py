"""S2 module: curvature-guided triangle-soup initialization.

Reads a coarse mesh (in the COLMAP scene frame), computes the S1 density map
(curvature + QEM importance), and samples seed points on the surface with
probability proportional to density -- high-curvature regions (nose/lips/eye
rims) get dense seeds, flat regions (cheeks/forehead) get sparse ones.
Each seed also gets a local triangle scale from its k-NN spacing, so dense
regions start with proportionally smaller triangles.

Output: .npz with points (N,3) float32, scales (N,) float32, density (N,)
float32, consumed by src/diffsoup_train.py --init curvature. Also writes a
preview PLY of the seeds colored by density for visual verification.

CPU-only (numpy/scipy/trimesh) -- safe to run while a GPU job is training.

Usage:
    python src/curvature_init.py output/buddha_sfm/mesh_coarse.ply \
        --n-points 15000 --out output/buddha_curv_init.npz
"""

import argparse
import os
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curvature_density import density_map


def sample_points_by_density(mesh, vertex_density, n_points, floor=0.05, seed=0):
    """Sample surface points with probability ~ area * (floor + density).

    `floor` keeps flat regions from being starved entirely -- DiffSoup still
    needs some coverage there to optimize opacity/color.

    Returns (points (N,3), density_at_points (N,)).
    """
    rng = np.random.default_rng(seed)
    V = mesh.vertices.view(np.ndarray)
    F = mesh.faces

    w = floor + (1.0 - floor) * vertex_density
    face_w = mesh.area_faces * w[F].mean(axis=1)
    face_w = face_w / face_w.sum()

    fid = rng.choice(len(F), size=n_points, p=face_w)
    r1, r2 = rng.random(n_points), rng.random(n_points)
    s1 = np.sqrt(r1)
    b = np.column_stack([1.0 - s1, s1 * (1.0 - r2), s1 * r2])  # uniform barycentric

    pts = np.einsum("nk,nkj->nj", b, V[F[fid]])
    dens = np.einsum("nk,nk->n", b, vertex_density[F[fid]])
    return pts.astype(np.float32), dens.astype(np.float32)


def local_scales(points, knn=3, factor=0.25, pct_clip=(5, 95)):
    """Per-point triangle circumradius from local k-NN spacing.

    Mirrors the DiffSoup example's global `0.25 * nn_spacing(...)` but per
    point, so triangle size adapts to the local seed density. Percentile
    clipping kills outliers from sampling noise.
    """
    tree = cKDTree(points)
    d, _ = tree.query(points, k=knn + 1)
    spacing = d[:, 1:].mean(axis=1)
    lo, hi = np.percentile(spacing, pct_clip)
    return (factor * np.clip(spacing, lo, hi)).astype(np.float32)


def save_preview_ply(points, density, path):
    import matplotlib.pyplot as plt
    colors = (plt.get_cmap("turbo")(np.clip(density, 0, 1))[:, :3] * 255).astype(np.uint8)
    trimesh.PointCloud(points, colors=colors).export(path)


def build_init(mesh_file, n_points=15000, floor=0.05, knn=3, factor=0.25,
               rings=2, seed=0, crop_center=None, crop_radius=None):
    """Full S2 pipeline: mesh -> (optional sphere crop) -> density -> seeds + scales."""
    mesh = trimesh.load(mesh_file, process=True, force="mesh")
    if crop_center is not None and crop_radius is not None:
        dist = np.linalg.norm(mesh.triangles_center - np.asarray(crop_center), axis=1)
        keep = np.where(dist <= crop_radius)[0]
        if len(keep) == 0:
            raise SystemExit("crop removed every face — check --crop-center/--crop-radius")
        mesh = mesh.submesh([keep], append=True)
        print(f"[crop] kept {len(mesh.faces):,} faces within r={crop_radius} of {list(crop_center)}")
    density, _, _ = density_map(mesh, n_rings=rings)
    pts, dens = sample_points_by_density(mesh, density, n_points, floor=floor, seed=seed)
    scales = local_scales(pts, knn=knn, factor=factor)
    return pts, scales, dens, mesh


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mesh_file")
    ap.add_argument("--n-points", type=int, default=15000)
    ap.add_argument("--floor", type=float, default=0.05,
                    help="minimum sampling weight for flat (density=0) regions")
    ap.add_argument("--knn", type=int, default=3)
    ap.add_argument("--scale-factor", type=float, default=0.25,
                    help="circumradius = factor * local k-NN spacing")
    ap.add_argument("--rings", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--crop-center", type=float, nargs=3, default=None,
                    help="sphere-crop the mesh around XYZ before sampling (e.g. head only)")
    ap.add_argument("--crop-radius", type=float, default=None)
    ap.add_argument("--out", default=None, help="output .npz (default: <out-dir>/<name>_curv_init.npz)")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "output"))
    args = ap.parse_args()

    name = os.path.splitext(os.path.basename(args.mesh_file))[0]
    out_npz = args.out or os.path.join(args.out_dir, f"{name}_curv_init.npz")
    os.makedirs(os.path.dirname(os.path.abspath(out_npz)), exist_ok=True)

    pts, scales, dens, mesh = build_init(
        args.mesh_file, n_points=args.n_points, floor=args.floor,
        knn=args.knn, factor=args.scale_factor, rings=args.rings, seed=args.seed,
        crop_center=args.crop_center, crop_radius=args.crop_radius,
    )

    print(f"mesh: {len(mesh.vertices)} verts, {len(mesh.faces)} faces, bounds={mesh.bounds.tolist()}")
    print(f"seeds: {len(pts)} points")
    print(f"density at seeds: min={dens.min():.3f} median={np.median(dens):.3f} max={dens.max():.3f}")
    print(f"scales: min={scales.min():.5f} median={np.median(scales):.5f} max={scales.max():.5f}")

    np.savez(out_npz, points=pts, scales=scales, density=dens)
    print("saved:", out_npz)

    preview = os.path.splitext(out_npz)[0] + "_preview.ply"
    save_preview_ply(pts, dens, preview)
    print("saved:", preview)


if __name__ == "__main__":
    main()
