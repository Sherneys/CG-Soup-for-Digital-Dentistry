# src/make_masks.py
# Render per-view object masks (head-only silhouettes) for a COLMAP scene.
#
# The object center is estimated automatically as the least-squares
# convergence point of all camera viewing rays (an orbit capture looks at
# the subject), then the coarse mesh is cropped to a sphere around it and
# rasterized through every camera with DiffSoup (fully opaque) to get a
# binary silhouette per view.
#
# Outputs:
#   <scene_root>/masks_<downscale>/<image_name>.png   (white = object)
#   <out>/overlay_*.png                               (visual check, 3 views)
#
# Usage:
#   $env:PYTHONUTF8 = "1"
#   python src\make_masks.py --scene_root output\buddha_sfm\dense --downscale 4 `
#       --mesh output\buddha_sfm\mesh_coarse.ply --radius 0.8

from __future__ import annotations

import argparse
import os
import sys

_DIFFSOUP_ROOT = os.environ.get("DIFFSOUP_ROOT", r"D:\Project\diffsoup")
sys.path.insert(0, os.path.join(_DIFFSOUP_ROOT, "examples"))

import imageio.v2 as iio
import numpy as np
import torch
import trimesh

import diffsoup as ds
from utils import load_mipnerf360_scene, mvp_from_K_Tcw, project_vertices, read_points3D


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene_root", required=True)
    ap.add_argument("--mesh", required=True, help="coarse mesh in the same COLMAP frame")
    ap.add_argument("--downscale", type=int, default=4)
    ap.add_argument("--center", type=float, nargs=3, default=None,
                    help="object center XYZ (default: median of COLMAP points3D — "
                         "SfM features concentrate on the subject)")
    ap.add_argument("--radius", type=float, default=0.8,
                    help="crop sphere radius around the center")
    ap.add_argument("--dilate", type=int, default=2, help="mask dilation in pixels")
    ap.add_argument("--meanshift", type=int, default=8,
                    help="mean-shift iterations to settle the center on the object (0 = off)")
    ap.add_argument("--out_dir", default=None,
                    help="default: <scene_root>/masks_<downscale>")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_dir = args.out_dir or os.path.join(args.scene_root, f"masks_{args.downscale}")
    os.makedirs(out_dir, exist_ok=True)

    # all views (train + test) need masks
    frames, K, H, W = [], None, None, None
    for split in ("train", "test"):
        data = load_mipnerf360_scene(args.scene_root, split=split, downscale=args.downscale, device=device)
        frames += data["frames"]
        K, H, W = data["K"], data["H"], data["W"]
    print(f"[views] total={len(frames)} size={H}x{W}")

    center = np.array(args.center) if args.center else np.median(read_points3D(args.scene_root), axis=0)
    print(f"[center] start {np.round(center, 3).tolist()}  (auto={args.center is None})")

    mesh = trimesh.load(args.mesh, process=True, force="mesh")
    fc = mesh.triangles_center
    area = mesh.area_faces

    # mean-shift onto the object: move to the area-weighted centroid of faces
    # within the radius until stable — corrects a center that starts on the
    # object's edge (e.g. points3D median biased toward a detailed region)
    for it in range(args.meanshift):
        member = np.linalg.norm(fc - center, axis=1) <= args.radius
        if member.sum() == 0:
            break
        new_center = np.average(fc[member], axis=0, weights=area[member])
        shift = np.linalg.norm(new_center - center)
        center = new_center
        if shift < 1e-3:
            break
    if args.meanshift > 0:
        print(f"[center] refined {np.round(center, 3).tolist()}  ({it + 1} mean-shift iters)")

    dist = np.linalg.norm(fc - center, axis=1)
    print(f"[mesh] face-centroid distance quantiles: "
          f"10%={np.quantile(dist, .1):.3f} 25%={np.quantile(dist, .25):.3f} "
          f"50%={np.quantile(dist, .5):.3f} 75%={np.quantile(dist, .75):.3f} 90%={np.quantile(dist, .9):.3f}")

    keep = dist <= args.radius
    print(f"[crop] radius={args.radius} keeps {keep.sum():,} / {len(keep):,} faces")
    if keep.sum() == 0:
        raise SystemExit("crop removed everything — increase --radius")

    sub = mesh.submesh([np.where(keep)[0]], append=True)
    V = torch.from_numpy(np.asarray(sub.vertices, dtype=np.float32)).to(device)
    F = torch.from_numpy(np.asarray(sub.faces, dtype=np.int32)).to(device)

    # fully opaque alpha buffer at level 0
    alpha_src = ds.build_multires_triangle_color(F.shape[0], 0, 0, feat_dim=1).to(device)
    with torch.no_grad():
        alpha_src.fill_(10.0)
        alpha_acc = ds.accumulate_to_level(0, 0, alpha_src).sigmoid()

    z_near, z_far = 0.01, 100.0
    n_overlay = 0
    with torch.no_grad():
        for i, fr in enumerate(frames):
            MVP = mvp_from_K_Tcw(K, fr["Tcw"], (H, W), z_near=z_near, z_far=z_far, flip_z=True).unsqueeze(0)
            V_clip = project_vertices(V, MVP)
            rast = ds.rasterize_multires_triangle_alpha(
                (H, W), V_clip, F, level=0, alpha_src=alpha_acc, stochastic=False,
            )
            m = (rast[..., -1] > 0.5).float().view(1, 1, H, W)
            if args.dilate > 0:
                k = 2 * args.dilate + 1
                m = torch.nn.functional.max_pool2d(m, k, stride=1, padding=args.dilate)
            m_np = (m.view(H, W).cpu().numpy() * 255).astype(np.uint8)

            stem = os.path.splitext(os.path.basename(fr["img_path"]))[0]
            iio.imwrite(os.path.join(out_dir, f"{stem}.png"), m_np)

            if n_overlay < 3 and i % max(1, len(frames) // 3) == 0:
                img = (fr["image"].cpu().numpy() * 255).astype(np.uint8)
                ov = img.copy()
                ov[m_np < 128] = (ov[m_np < 128] * 0.25).astype(np.uint8)
                iio.imwrite(os.path.join(out_dir, f"overlay_{stem}.png"), ov)
                n_overlay += 1

    coverage = []
    for f in sorted(os.listdir(out_dir)):
        if f.startswith("overlay"):
            continue
        m = iio.imread(os.path.join(out_dir, f))
        coverage.append((m > 127).mean())
    print(f"[masks] {len(coverage)} saved → {out_dir}  coverage min={min(coverage):.1%} "
          f"median={float(np.median(coverage)):.1%} max={max(coverage):.1%}")


if __name__ == "__main__":
    main()
