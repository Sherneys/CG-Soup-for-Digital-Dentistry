"""S4 module: verify absolute scale between intraoral scan and TrueDepth (Track B).

The intraoral scanner has absolute scale, so within one arch (rigid body) the
inter-marker distances measured by the TrueDepth localizer must match the
distances in the dental scan. Step B4 in docs/ARCHITECTURE.md:

    |d_camera(i, j) - d_dental(i, j)| <= 0.1 mm  for all marker pairs (i, j)

Only same-arch pairs are compared: the jaw moves, so upper-lower distances
are not rigid. Observed positions are aggregated as the per-marker median
over all frames before comparison (use --frame to check a single frame).

Exit code: 0 = pass, 1 = fail (usable in shell pipelines / CI).

Usage:
    python scale_verify.py dental_markers.json points3d.json \
        [--tolerance-mm 0.1] [--frame N] [--report report.json]
"""

import argparse
import itertools
import json
import sys
from dataclasses import dataclass

import numpy as np

DEFAULT_TOLERANCE_MM = 0.1


def pairwise_distances(points: dict[str, np.ndarray]) -> dict[tuple[str, str], float]:
    """Euclidean distance for every unordered pair of labeled points."""
    return {
        (a, b): float(np.linalg.norm(np.asarray(points[a], dtype=float)
                                     - np.asarray(points[b], dtype=float)))
        for a, b in itertools.combinations(sorted(points), 2)
    }


def aggregate_frames(frames: list[dict]) -> dict[str, np.ndarray]:
    """Per-marker median position over all frames (robust to outlier frames)."""
    samples: dict[str, list] = {}
    for f in frames:
        for label, xyz in f["points"].items():
            samples.setdefault(label, []).append(xyz)
    return {label: np.median(np.asarray(v, dtype=float), axis=0)
            for label, v in samples.items()}


@dataclass(frozen=True)
class PairCheck:
    pair: tuple[str, str]
    dental_mm: float
    observed_mm: float

    @property
    def delta_mm(self) -> float:
        return self.observed_mm - self.dental_mm


@dataclass(frozen=True)
class ScaleReport:
    pairs: tuple[PairCheck, ...]
    tolerance_mm: float

    @property
    def max_abs_delta_mm(self) -> float:
        return max((abs(p.delta_mm) for p in self.pairs), default=float("nan"))

    @property
    def passed(self) -> bool:
        return len(self.pairs) > 0 and self.max_abs_delta_mm <= self.tolerance_mm

    def to_dict(self) -> dict:
        return {
            "tolerance_mm": self.tolerance_mm,
            "passed": self.passed,
            "max_abs_delta_mm": self.max_abs_delta_mm,
            "pairs": [
                {"pair": list(p.pair), "dental_mm": p.dental_mm,
                 "observed_mm": p.observed_mm, "delta_mm": p.delta_mm}
                for p in self.pairs
            ],
        }


def verify_scale(dental: dict[str, dict[str, np.ndarray]],
                 observed: dict[str, np.ndarray],
                 tolerance_mm: float = DEFAULT_TOLERANCE_MM) -> ScaleReport:
    """Compare same-arch inter-marker distances: dental scan vs observed points.

    dental: {"upper": {label: xyz_mm}, "lower": {label: xyz_mm}}
    observed: {label: xyz_mm} in any rigid frame (e.g. camera frame).
    """
    checks: list[PairCheck] = []
    for arch_points in dental.values():
        ref = pairwise_distances(arch_points)
        common = {k: observed[k] for k in arch_points if k in observed}
        obs = pairwise_distances(common)
        for pair, d_obs in obs.items():
            checks.append(PairCheck(pair=pair, dental_mm=ref[pair], observed_mm=d_obs))
    return ScaleReport(pairs=tuple(checks), tolerance_mm=tolerance_mm)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dental_markers", help="dental_markers.json (mm, dental frame)")
    ap.add_argument("points3d", help="points3d.json from marker_localizer.py")
    ap.add_argument("--tolerance-mm", type=float, default=DEFAULT_TOLERANCE_MM)
    ap.add_argument("--frame", type=int, help="check a single frame instead of the median")
    ap.add_argument("--report", help="optional path for a JSON report")
    args = ap.parse_args()

    with open(args.dental_markers) as fh:
        dental = {arch: {k: np.asarray(v, dtype=float) for k, v in pts.items()}
                  for arch, pts in json.load(fh).items()}
    with open(args.points3d) as fh:
        frames = json.load(fh)["frames"]

    if args.frame is not None:
        frames = [f for f in frames if int(f["frame"]) == args.frame]
        if not frames:
            raise SystemExit(f"frame {args.frame} not found in {args.points3d}")
    observed = aggregate_frames(frames)

    report = verify_scale(dental, observed, args.tolerance_mm)
    for p in sorted(report.pairs, key=lambda p: -abs(p.delta_mm)):
        flag = "OK  " if abs(p.delta_mm) <= report.tolerance_mm else "FAIL"
        print(f"{flag} {p.pair[0]}-{p.pair[1]}: dental={p.dental_mm:.3f}mm "
              f"observed={p.observed_mm:.3f}mm delta={p.delta_mm:+.3f}mm")

    if args.report:
        with open(args.report, "w") as fh:
            json.dump(report.to_dict(), fh, indent=2)
        print("saved:", args.report)

    if not report.pairs:
        print("no common marker pairs to compare — check labels")
        sys.exit(1)
    print(f"max |delta| = {report.max_abs_delta_mm:.3f} mm "
          f"(tolerance {report.tolerance_mm} mm) -> {'PASS' if report.passed else 'FAIL'}")
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
