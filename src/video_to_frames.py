"""Extract sharp frames from an orbit video for the SfM pipeline (set A).

Splits the video into N equal time windows and keeps the sharpest frame in
each (variance of Laplacian) — this dodges motion blur, the main killer of
SIFT matching on handheld sweeps. Output images go straight into
src/sfm_pipeline.py.

Usage:
    python src\\video_to_frames.py data\\myface\\sweep.mp4 --out data\\myface\\images --n-frames 70
    python src\\sfm_pipeline.py data\\myface\\images --workspace output\\myface_sfm
"""

import argparse
import os

import cv2
import numpy as np


def sharpness(gray_small: np.ndarray) -> float:
    return float(cv2.Laplacian(gray_small, cv2.CV_64F).var())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video")
    ap.add_argument("--out", required=True, help="output image folder")
    ap.add_argument("--n-frames", type=int, default=70,
                    help="target number of extracted frames")
    ap.add_argument("--rotate", type=int, default=None, choices=[0, 90, 180, 270],
                    help="force rotation (default: trust video metadata)")
    ap.add_argument("--quality", type=int, default=95, help="JPEG quality")
    ap.add_argument("--probe-stride", type=int, default=2,
                    help="evaluate sharpness on every k-th frame in a window")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {args.video}")
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)  # honor phone rotation metadata

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    if total <= 0:
        raise SystemExit("video reports no frames — re-encode it (e.g. with ffmpeg) and retry")
    n_out = min(args.n_frames, total)
    print(f"[video] {total} frames @ {fps:.1f} fps ({total / fps:.1f}s) -> extracting {n_out}")

    rot_map = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    edges = np.linspace(0, total, n_out + 1).astype(int)

    saved, scores = 0, []
    for w in range(n_out):
        best, best_score = None, -1.0
        idx = w * 0  # noqa: F841  (window-local frame counter follows)
        cap.set(cv2.CAP_PROP_POS_FRAMES, edges[w])
        for j in range(edges[w], edges[w + 1]):
            ok, frame = cap.read()
            if not ok:
                break
            if (j - edges[w]) % args.probe_stride != 0:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (gray.shape[1] // 4, gray.shape[0] // 4))
            s = sharpness(small)
            if s > best_score:
                best, best_score = frame, s
        if best is None:
            continue
        if args.rotate:
            best = cv2.rotate(best, rot_map[args.rotate])
        cv2.imwrite(os.path.join(args.out, f"{saved:04d}.jpg"), best,
                    [cv2.IMWRITE_JPEG_QUALITY, args.quality])
        scores.append(best_score)
        saved += 1

    cap.release()
    print(f"[frames] saved {saved} -> {args.out}")
    print(f"[sharpness] min={min(scores):.1f} median={float(np.median(scores)):.1f} max={max(scores):.1f}")
    print(f"next: python src\\sfm_pipeline.py {args.out} --workspace output\\<name>_sfm")


if __name__ == "__main__":
    main()
