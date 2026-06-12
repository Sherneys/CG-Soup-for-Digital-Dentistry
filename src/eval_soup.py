# src/eval_soup.py
# Evaluate a trained DiffSoup checkpoint on the test split: PSNR / SSIM / LPIPS.
#
# Complements src/diffsoup_train.py (which reports only PSNR/SSIM) — the
# project KPI requires LPIPS as well.  Works on any final_params.pt without
# retraining, so old runs can be re-scored.
#
# LPIPS note: uses lpips with the VGG backbone (v0.1) — keep this identical
# across all baselines for fair comparison.
#
# Usage:
#   $env:PYTHONUTF8 = "1"
#   python src\eval_soup.py --ckpt output\diffsoup_buddha_curv_d4_f5k\final_params.pt `
#       --scene_root output\buddha_sfm\dense --downscale 4

from __future__ import annotations

import argparse
import os
import sys

_DIFFSOUP_ROOT = os.environ.get("DIFFSOUP_ROOT", r"D:\Project\diffsoup")
sys.path.insert(0, os.path.join(_DIFFSOUP_ROOT, "examples"))

import lpips as lpips_lib
import numpy as np
import torch
from pytorch_msssim import ssim

import diffsoup as ds
from utils import load_mipnerf360_scene, mvp_from_K_Tcw, project_vertices, psnr_fn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffsoup_train import load_view_masks, masked_psnr, mask_bbox_crop


def render_view(ckpt, MVP, MVP_inv, device):
    H, W, feat_dim, Rmax = ckpt["H"], ckpt["W"], ckpt["feat_dim"], ckpt["Rmax"]
    V_clip = project_vertices(ckpt["V"], MVP)
    rast_out = ds.rasterize_multires_triangle_alpha(
        (H, W), V_clip, ckpt["F"],
        level=Rmax,
        alpha_src=ckpt["alpha_acc"],
        stochastic=False,
    )
    feat = ds.multires_triangle_color(
        rast_out, level=Rmax, feat=ckpt["feat_acc"],
    ).view(-1, H, W, feat_dim)
    feat = torch.cat([feat, ds.encode_view_dir_sh2(rast_out, MVP_inv)], dim=-1)
    color = ckpt["mlp"].forward(feat, mask=rast_out[..., -1] > 0).view(1, H, W, 3)
    return color.squeeze(0).clamp(0, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--scene_root", required=True)
    ap.add_argument("--downscale", type=int, default=4)
    ap.add_argument("--lpips_net", default="vgg", choices=["vgg", "alex"])
    ap.add_argument("--masks", default=None,
                    help="mask folder from src/make_masks.py — score inside masks only")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    raw = torch.load(args.ckpt, map_location=device, weights_only=False)
    mlp = ds.ColorMLP(
        input_dim=raw["feat_dim"] + 9, hidden_dim=16, n_layers=2, output_dim=3,
    ).to(device)
    mlp.load_state_dict(raw["color_mlp"])
    mlp.eval()
    ckpt = {
        "V": raw["V"].to(device), "F": raw["F"].to(device),
        "feat_acc": raw["feat_acc"].to(device), "alpha_acc": raw["alpha_acc"].to(device),
        "H": raw["H"], "W": raw["W"], "feat_dim": raw["feat_dim"],
        "Rmax": raw["Rmax"], "mlp": mlp,
    }
    K = raw["K"].to(device)
    flip_z = raw["flip_z"]
    print(f"[ckpt] faces={ckpt['F'].shape[0]:,} verts={ckpt['V'].shape[0]:,} "
          f"Rmax={ckpt['Rmax']} init={raw.get('init', '?')} seed={raw.get('seed', '?')}")

    test_data = load_mipnerf360_scene(
        args.scene_root, split="test", downscale=args.downscale, device=device,
    )
    frames = test_data["frames"]
    assert test_data["H"] == ckpt["H"] and test_data["W"] == ckpt["W"], \
        f"resolution mismatch: ckpt {ckpt['H']}x{ckpt['W']} vs scene {test_data['H']}x{test_data['W']} — check --downscale"

    lpips_model = lpips_lib.LPIPS(net=args.lpips_net, verbose=False).to(device)

    test_masks = load_view_masks(args.masks, frames, device) if args.masks else None

    z_near_test, z_far = 0.5, 100.0
    psnrs, ssims, lpipss = [], [], []
    with torch.no_grad():
        for i, fr in enumerate(frames):
            MVP = mvp_from_K_Tcw(
                K, fr["Tcw"], (ckpt["H"], ckpt["W"]),
                z_near=z_near_test, z_far=z_far, flip_z=flip_z,
            ).unsqueeze(0)
            pred = render_view(ckpt, MVP, torch.inverse(MVP).contiguous(), device)
            gt = fr["image"].clamp(0, 1)

            if test_masks is not None:
                tm = test_masks[i]
                psnrs.append(masked_psnr(pred, gt, tm))
                pc, gc = mask_bbox_crop(pred, gt, tm)
                pred_nchw = pc.permute(2, 0, 1).unsqueeze(0)
                gt_nchw = gc.permute(2, 0, 1).unsqueeze(0)
            else:
                psnrs.append(float(psnr_fn(pred, gt).item()))
                pred_nchw = pred.permute(2, 0, 1).unsqueeze(0)
                gt_nchw = gt.permute(2, 0, 1).unsqueeze(0)
            ssims.append(float(ssim(gt_nchw, pred_nchw, data_range=1.0).item()))
            lpipss.append(float(lpips_model(pred_nchw * 2 - 1, gt_nchw * 2 - 1).item()))

    name = os.path.basename(os.path.dirname(os.path.abspath(args.ckpt)))
    tag = " (masked)" if test_masks is not None else ""
    print(f"[result] {name}{tag}  PSNR={np.mean(psnrs):.3f}  SSIM={np.mean(ssims):.4f}  LPIPS={np.mean(lpipss):.4f}")

    suffix = "_masked" if test_masks is not None else ""
    out_txt = os.path.join(os.path.dirname(args.ckpt), "test_views", f"metrics_lpips{suffix}.txt")
    os.makedirs(os.path.dirname(out_txt), exist_ok=True)
    with open(out_txt, "w") as f:
        f.write(f"lpips_net={args.lpips_net} downscale={args.downscale} masked={test_masks is not None}\n")
        for i, (p, s, l) in enumerate(zip(psnrs, ssims, lpipss)):
            f.write(f"{i:04d} PSNR={p:.3f} SSIM={s:.4f} LPIPS={l:.4f}\n")
        f.write(f"\nmean PSNR={np.mean(psnrs):.3f} SSIM={np.mean(ssims):.4f} LPIPS={np.mean(lpipss):.4f}\n")
    print(f"[save] {out_txt}")


if __name__ == "__main__":
    main()
