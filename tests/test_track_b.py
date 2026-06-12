"""Track B unit + synthetic end-to-end tests (no clinic data required).

Synthetic ground truth replaces clinic recordings until real data arrives:
known rigid transforms are applied to fabricated marker sets, and the
pipeline must recover them within the project specs (fit RMSE <= 0.5 mm,
scale tolerance 0.1 mm).

Run:  pytest tests/ -v
"""

import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jaw_tracker import (  # noqa: E402
    invert,
    match_by_geometry,
    relabel_frames,
    rigid_transform_svd,
    solve_arch_pose,
    to_homogeneous,
    track_jaw,
)
from marker_localizer import (  # noqa: E402
    CameraIntrinsics,
    back_project,
    localize_frame,
    sample_depth,
)
from registration import apply_transform, register_points  # noqa: E402
from scale_verify import aggregate_frames, pairwise_distances, verify_scale  # noqa: E402


def rotation(axis, angle_rad: float) -> np.ndarray:
    """Rodrigues rotation matrix about a (not necessarily unit) axis."""
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle_rad) * K + (1 - math.cos(angle_rad)) * (K @ K)


# Synthetic marker layouts (mm, dental frame) — 4 dots per arch like the clinic protocol
UPPER = {
    "U1": np.array([-15.0, 0.0, 5.0]),
    "U2": np.array([-5.0, 8.0, 2.0]),
    "U3": np.array([5.0, 8.0, 2.0]),
    "U4": np.array([15.0, 0.0, 5.0]),
}
LOWER = {
    "L1": np.array([-14.0, -2.0, -5.0]),
    "L2": np.array([-4.0, 6.0, -8.0]),
    "L3": np.array([6.0, 6.0, -8.0]),
    "L4": np.array([14.0, -2.0, -5.0]),
}
DENTAL = {"upper": UPPER, "lower": LOWER}


def transform_points(points: dict, R: np.ndarray, t: np.ndarray,
                     noise_mm: float = 0.0, rng=None) -> dict:
    out = {}
    for k, p in points.items():
        q = R @ p + t
        if noise_mm > 0:
            q = q + rng.normal(0, noise_mm, 3)
        out[k] = q
    return out


# ---------------------------------------------------------------- jaw_tracker

class TestRigidTransformSVD:
    def test_recovers_exact_transform(self):
        rng = np.random.default_rng(0)
        R_true = rotation([1, 2, 3], 0.7)
        t_true = np.array([10.0, -5.0, 30.0])
        src = rng.normal(0, 10, (6, 3))

        R, t, rmse = rigid_transform_svd(src, src @ R_true.T + t_true)

        np.testing.assert_allclose(R, R_true, atol=1e-9)
        np.testing.assert_allclose(t, t_true, atol=1e-9)
        assert rmse < 1e-9

    def test_noisy_points_meet_spec(self):
        rng = np.random.default_rng(1)
        R_true = rotation([0, 1, 0], 0.3)
        t_true = np.array([0.0, 0.0, 400.0])
        src = np.array(list(UPPER.values()))
        dst = src @ R_true.T + t_true + rng.normal(0, 0.05, src.shape)

        R, t, rmse = rigid_transform_svd(src, dst)

        assert rmse <= 0.5  # project spec: RMSE <= 0.5 mm
        assert np.linalg.norm(t - t_true) < 0.5

    def test_no_reflection_on_planar_points(self):
        # coplanar markers are the degenerate case that can flip the SVD solution
        src = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0], [10, 10, 0]], dtype=float)
        R_true = rotation([1, 0, 0], 1.2)

        R, _, _ = rigid_transform_svd(src, src @ R_true.T)

        assert np.linalg.det(R) == pytest.approx(1.0)
        np.testing.assert_allclose(R, R_true, atol=1e-9)

    def test_rejects_too_few_points(self):
        with pytest.raises(ValueError):
            rigid_transform_svd(np.zeros((2, 3)), np.zeros((2, 3)))


class TestArchPose:
    def test_uses_common_labels_only(self):
        R_true = rotation([0, 0, 1], 0.5)
        t_true = np.array([1.0, 2.0, 3.0])
        observed = transform_points(UPPER, R_true, t_true)
        observed["stray"] = np.array([99.0, 99.0, 99.0])

        pose = solve_arch_pose(UPPER, observed)

        assert pose.n_markers == 4
        np.testing.assert_allclose(pose.T, to_homogeneous(R_true, t_true), atol=1e-9)

    def test_none_when_markers_missing(self):
        observed = {"U1": UPPER["U1"], "U2": UPPER["U2"]}
        assert solve_arch_pose(UPPER, observed) is None


class TestAutoLabeling:
    def test_match_by_geometry_recovers_labels(self):
        R = rotation([3, 1, 2], 1.1)
        moved = transform_points(UPPER, R, np.array([5.0, 6.0, 7.0]))
        observed = {f"upper_{i}": moved[k] for i, k in enumerate(["U3", "U1", "U4", "U2"])}

        mapping = match_by_geometry(UPPER, observed)

        assert mapping == {"upper_0": "U3", "upper_1": "U1",
                           "upper_2": "U4", "upper_3": "U2"}

    def test_relabel_frames_applies_first_frame_mapping(self):
        R = rotation([0, 1, 0], 0.2)
        t = np.array([0.0, 0.0, 350.0])
        points = {**{f"upper_{i}": (R @ UPPER[k] + t)
                     for i, k in enumerate(["U1", "U2", "U3", "U4"])},
                  **{f"lower_{i}": (R @ LOWER[k] + t)
                     for i, k in enumerate(["L1", "L2", "L3", "L4"])}}
        frames = [{"frame": 0, "t_ms": 0.0,
                   "points": {k: v.tolist() for k, v in points.items()}}]

        relabeled = relabel_frames(DENTAL, frames)

        assert set(relabeled[0]["points"]) == set(UPPER) | set(LOWER)


class TestTrackJaw:
    def test_recovers_hinge_opening_motion(self):
        rng = np.random.default_rng(2)
        # camera pose: both arches seen from ~40 cm away at an angle
        R_cam = rotation([0, 1, 0], 0.4)
        t_cam = np.array([20.0, -10.0, 400.0])
        hinge_point = np.array([0.0, -40.0, -10.0])  # condyle-ish axis offset

        frames, truths = [], []
        for i, angle in enumerate(np.linspace(0, 0.35, 8)):  # opening up to ~20 deg
            R_jaw = rotation([1, 0, 0], angle)
            t_jaw = hinge_point - R_jaw @ hinge_point
            lower_dental = transform_points(LOWER, R_jaw, t_jaw)
            cam_pts = {
                **transform_points(UPPER, R_cam, t_cam, noise_mm=0.05, rng=rng),
                **transform_points(lower_dental, R_cam, t_cam, noise_mm=0.05, rng=rng),
            }
            frames.append({"frame": i, "t_ms": i * 33.3, "points": cam_pts})
            truths.append(to_homogeneous(R_jaw, t_jaw))

        result = track_jaw(DENTAL, frames)

        assert len(result) == len(frames)
        for jf, T_true in zip(result, truths):
            # rotation error in degrees
            dR = jf.T_jaw[:3, :3] @ T_true[:3, :3].T
            angle_err = math.degrees(math.acos(np.clip((np.trace(dR) - 1) / 2, -1, 1)))
            assert angle_err < 1.0
            assert np.linalg.norm(jf.T_jaw[:3, 3] - T_true[:3, 3]) < 0.5
            assert jf.upper.rmse_mm <= 0.5 and jf.lower.rmse_mm <= 0.5

    def test_identity_at_bite_pose(self):
        cam_pts = {**UPPER, **LOWER}  # camera frame == dental frame, jaw closed
        result = track_jaw(DENTAL, [{"frame": 0, "t_ms": 0.0, "points": cam_pts}])
        np.testing.assert_allclose(result[0].T_jaw, np.eye(4), atol=1e-9)

    def test_skips_frames_with_occluded_arch(self):
        cam_pts = {**UPPER, "L1": LOWER["L1"]}  # lower arch mostly occluded
        result = track_jaw(DENTAL, [{"frame": 0, "t_ms": 0.0, "points": cam_pts}])
        assert result == []


class TestTransforms:
    def test_invert_round_trip(self):
        T = to_homogeneous(rotation([1, 1, 0], 0.8), np.array([3.0, -2.0, 9.0]))
        np.testing.assert_allclose(invert(T) @ T, np.eye(4), atol=1e-12)


# ------------------------------------------------------------ marker_localizer

K = CameraIntrinsics(fx=590.0, fy=590.0, cx=320.0, cy=240.0, width=640, height=480)


class TestBackProjection:
    def test_round_trip_projection(self):
        p_mm = np.array([12.0, -8.0, 410.0])  # camera frame, ~41 cm away
        u = K.fx * p_mm[0] / p_mm[2] + K.cx
        v = K.fy * p_mm[1] / p_mm[2] + K.cy

        recovered = back_project(u, v, p_mm[2] / 1000.0, K)

        np.testing.assert_allclose(recovered, p_mm, atol=1e-9)

    def test_sample_depth_median_ignores_invalid(self):
        depth = np.full((480, 640), np.nan, dtype=np.float32)
        depth[238:243, 318:323] = 0.4
        depth[240, 320] = 0.0  # invalid hole at the center

        assert sample_depth(depth, 320, 240) == pytest.approx(0.4)

    def test_sample_depth_out_of_bounds_is_nan(self):
        depth = np.full((480, 640), 0.4, dtype=np.float32)
        assert math.isnan(sample_depth(depth, -5, 10))
        assert math.isnan(sample_depth(depth, 10, 1000))

    def test_localize_frame_scales_rgb_coordinates(self):
        depth = np.full((480, 640), 0.4, dtype=np.float32)
        # detection at the center of a 1920x1440 RGB frame -> depth pixel (320, 240)
        markers = [{"id": "upper_0", "u": 960.0, "v": 720.0}]

        points = localize_frame(markers, depth, K, rgb_size=(1920, 1440))

        np.testing.assert_allclose(points["upper_0"], [0.0, 0.0, 400.0], atol=1e-9)

    def test_localize_frame_drops_markers_without_depth(self):
        depth = np.full((480, 640), np.nan, dtype=np.float32)
        markers = [{"id": "upper_0", "u": 320.0, "v": 240.0}]
        assert localize_frame(markers, depth, K) == {}


# ---------------------------------------------------------------- scale_verify

class TestScaleVerify:
    def test_passes_for_rigidly_moved_markers(self):
        moved = transform_points({**UPPER, **LOWER},
                                 rotation([1, 0, 1], 0.9), np.array([4.0, 5.0, 6.0]))
        report = verify_scale(DENTAL, moved)
        assert report.passed
        assert report.max_abs_delta_mm == pytest.approx(0.0, abs=1e-9)

    def test_fails_for_scaled_markers(self):
        scaled = {k: 1.01 * v for k, v in {**UPPER, **LOWER}.items()}  # 1% scale error
        report = verify_scale(DENTAL, scaled)
        assert not report.passed
        assert report.max_abs_delta_mm > 0.1

    def test_ignores_cross_arch_pairs(self):
        report = verify_scale(DENTAL, {**UPPER, **LOWER})
        n_same_arch = len(pairwise_distances(UPPER)) + len(pairwise_distances(LOWER))
        assert len(report.pairs) == n_same_arch

    def test_aggregate_frames_takes_median(self):
        frames = [
            {"points": {"U1": [0.0, 0.0, 0.0]}},
            {"points": {"U1": [0.0, 0.0, 2.0]}},
            {"points": {"U1": [0.0, 0.0, 100.0]}},  # outlier frame
        ]
        np.testing.assert_allclose(aggregate_frames(frames)["U1"], [0.0, 0.0, 2.0])


# ---------------------------------------------------------------- registration

class TestRegistration:
    def test_recovers_known_transform(self):
        R_true = rotation([2, 0, 1], 0.6)
        t_true = np.array([-7.0, 3.0, 12.0])
        src = {**UPPER, **LOWER}
        dst = transform_points(src, R_true, t_true)

        T, rmse, n = register_points(src, dst)

        assert n == 8
        assert rmse < 1e-9
        np.testing.assert_allclose(T, to_homogeneous(R_true, t_true), atol=1e-9)

    def test_apply_transform_round_trip(self):
        T = to_homogeneous(rotation([0, 1, 1], 0.4), np.array([1.0, 2.0, 3.0]))
        pts = np.array(list(UPPER.values()))
        np.testing.assert_allclose(apply_transform(invert(T), apply_transform(T, pts)),
                                   pts, atol=1e-12)

    def test_rejects_insufficient_overlap(self):
        with pytest.raises(ValueError):
            register_points({"A": UPPER["U1"]}, {"A": UPPER["U1"]})


# -------------------------------------------------------------- marker_detector

cv2 = pytest.importorskip("cv2")
from marker_detector import DetectorConfig, MarkerTracker, detect_in_frame  # noqa: E402


def synthetic_frame(upper_centers, lower_centers, radius=8):
    """BGR frame with blue dots (upper arch) and green dots (lower arch)."""
    img = np.full((480, 640, 3), 255, dtype=np.uint8)
    for u, v in upper_centers:
        cv2.circle(img, (u, v), radius, (255, 0, 0), -1)  # blue in BGR
    for u, v in lower_centers:
        cv2.circle(img, (u, v), radius, (0, 200, 0), -1)  # green in BGR
    return img


class TestMarkerDetector:
    def test_detects_dots_with_subpixel_accuracy(self):
        upper = [(100, 100), (200, 120)]
        lower = [(150, 300)]
        img = synthetic_frame(upper, lower)

        detections = detect_in_frame(img, DetectorConfig())

        found = {"upper": [], "lower": []}
        for d in detections:
            found[d.arch].append((d.u, d.v))
        assert len(found["upper"]) == 2 and len(found["lower"]) == 1
        for (u, v), (du, dv) in zip(sorted(upper), sorted(found["upper"])):
            assert abs(u - du) < 1.0 and abs(v - dv) < 1.0

    def test_rejects_non_circular_blobs(self):
        img = np.full((480, 640, 3), 255, dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (220, 112), (255, 0, 0), -1)  # elongated bar

        detections = detect_in_frame(img, DetectorConfig())

        assert detections == []

    def test_tracker_keeps_ids_across_motion(self):
        tracker = MarkerTracker(max_jump_px=60.0)
        frame1 = detect_in_frame(synthetic_frame([(100, 100), (300, 100)], []),
                                 DetectorConfig())
        frame2 = detect_in_frame(synthetic_frame([(110, 105), (310, 95)], []),
                                 DetectorConfig())

        ids1 = {round(d.u, -1): mid for mid, d in tracker.update(frame1)}
        ids2 = {round(d.u, -1): mid for mid, d in tracker.update(frame2)}

        assert ids1[100.0] == ids2[110.0]
        assert ids1[300.0] == ids2[310.0]

    def test_tracker_assigns_new_id_for_new_marker(self):
        tracker = MarkerTracker(max_jump_px=60.0)
        tracker.update(detect_in_frame(synthetic_frame([(100, 100)], []), DetectorConfig()))
        labeled = tracker.update(detect_in_frame(
            synthetic_frame([(102, 101), (400, 200)], []), DetectorConfig()))

        ids = sorted(mid for mid, _ in labeled)
        assert ids == ["upper_0", "upper_1"]
