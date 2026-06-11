"""SfM pipeline: multi-view images -> coarse mesh via COLMAP (CUDA).

Runs feature extraction -> matching -> sparse reconstruction -> dense stereo
-> fusion -> Poisson mesh. Output mesh feeds src/curvature_density.py.

Tested with COLMAP 4.1.0.dev0 (release 4.0.4) — note 4.x option names
(--FeatureExtraction.use_gpu, not 3.x --SiftExtraction.use_gpu).

Usage:
    python src/sfm_pipeline.py data/buddha/images --workspace output/buddha_sfm
"""

import argparse
import os
import subprocess
import sys
import time

DEFAULT_COLMAP = r"D:\Tools\colmap\bin\colmap.exe"


def run(colmap, command, **options):
    args = [colmap, command]
    for key, value in options.items():
        args += [f"--{key}", str(value)]
    print(f"\n=== colmap {command} ===", flush=True)
    t0 = time.time()
    result = subprocess.run(args)
    if result.returncode != 0:
        sys.exit(f"colmap {command} failed (exit {result.returncode})")
    print(f"=== {command} done in {time.time() - t0:.1f}s ===", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_path")
    parser.add_argument("--workspace", required=True, help="output folder for database/sparse/dense")
    parser.add_argument("--colmap", default=DEFAULT_COLMAP)
    parser.add_argument("--max-image-size", type=int, default=2000,
                        help="downscale long side for dense stereo (VRAM 12GB)")
    parser.add_argument("--skip-dense", action="store_true", help="stop after sparse reconstruction")
    args = parser.parse_args()

    ws = os.path.abspath(args.workspace)
    database = os.path.join(ws, "database.db")
    sparse = os.path.join(ws, "sparse")
    dense = os.path.join(ws, "dense")
    mesh = os.path.join(ws, "mesh_poisson.ply")
    os.makedirs(sparse, exist_ok=True)

    run(args.colmap, "feature_extractor",
        database_path=database,
        image_path=args.image_path,
        **{"ImageReader.single_camera": 1,
           "FeatureExtraction.use_gpu": 1})

    run(args.colmap, "exhaustive_matcher",
        database_path=database,
        **{"FeatureMatching.use_gpu": 1})

    run(args.colmap, "mapper",
        database_path=database,
        image_path=args.image_path,
        output_path=sparse)

    model = os.path.join(sparse, "0")
    if not os.path.isdir(model):
        sys.exit("mapper produced no model — check image overlap/quality")

    if args.skip_dense:
        print(f"\nsparse model: {model}")
        return

    run(args.colmap, "image_undistorter",
        image_path=args.image_path,
        input_path=model,
        output_path=dense,
        max_image_size=args.max_image_size)

    run(args.colmap, "patch_match_stereo",
        workspace_path=dense,
        **{"PatchMatchStereo.geom_consistency": 1,
           "PatchMatchStereo.max_image_size": args.max_image_size})

    run(args.colmap, "stereo_fusion",
        workspace_path=dense,
        output_path=os.path.join(dense, "fused.ply"))

    run(args.colmap, "poisson_mesher",
        input_path=os.path.join(dense, "fused.ply"),
        output_path=mesh)

    print(f"\ncoarse mesh: {mesh}")
    print(f"next: python src/curvature_density.py {mesh} --out-dir output")


if __name__ == "__main__":
    main()
