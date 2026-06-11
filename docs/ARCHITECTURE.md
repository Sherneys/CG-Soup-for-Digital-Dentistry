# System Architecture — CG-Soup + JawTrack (CP-2026-A4)

**Team 4** | Last updated: 2026-06-11

---

## Overview

Two independent tracks that converge at Track C (Integration):

```
Track A: Multi-view Face Photos
  └─► COLMAP SfM ──► Curvature Analysis ──► CG-Soup Init ──► DiffSoup ──► 3D Face Model
                                                                               │
Track B: Fiducial Dot Markers on Teeth                                         │
  └─► Intraoral Scan (WITH Markers) ─► Marker 3D Positions (Dental Frame)     │
         │                                                                      │
  iPhone TrueDepth Video ──► Marker Detection ──► 6DOF per Frame ─────────────┤
                                                                               │
Track C: Integration ◄─────────────────────────────────────────────────────────┘
  └─► Registration ──► CI-TRANSFORM (JSON/XML) ──► Exocad / Team 1 API
```

---

## Track A — CG-Soup Pipeline (Extra-Oral Face)

### Input
- ≥ 40 multi-view face photographs taken while patient smiles (extra-oral, full face)
- 1 additional "smile showing teeth" set for face ↔ dental bridge registration

### Step A1 — Structure from Motion (COLMAP)

```
Photos (≥40 views) ──► COLMAP ──┬─► Camera Poses (R, t, intrinsics per frame)
                                 └─► Coarse Point Cloud
```

- Tool: COLMAP (open-source)
- Output: `cameras.txt`, `images.txt`, `points3D.txt`

### Step A2 — Curvature Analysis

```
Coarse Mesh ──► vertex_rings(n=2) ──► Quadric Fit (tangent frame)
                                           ├─► κ₁, κ₂ (Principal Curvatures)
                                           └─► QEM per vertex
                                                    │
                                               curvedness = √((κ₁²+κ₂²)/2)
                                                    │
                                          density = 0.5·normalize(curvedness)
                                                  + 0.5·normalize(QEM)
                                                    │
                                          Laplacian smooth (10 iters)
                                                    │
                                               Density Map (PLY + PNG)
```

- Implementation: `src/curvature_density.py` ✅ (Sprint S1 complete)
- High density (hot): nose, lips, ears, eye rims, chin
- Low density (cool): cheeks, forehead

### Step A3 — CG-Soup Initialization

```
Density Map ──► Sample N triangle positions ──► Initialize Triangle Soup
                (dense where curvature is high)   (vertex positions + opacity)
```

### Step A4 — DiffSoup Optimization

```
Triangle Soup (init) ──► Differentiable Rasterizer ──┬─► Rendered Image
                                                       │        │
Target Image ◄─────────────────────────────────────────┘        │
                                                                  ▼
                                               Loss = L_photo + λ_ang·L_angular
                                                             + λ_d·L_dihedral
                                                             + λ_c·L_color
                                                             + λ_e·L_edge_grad
                                                                  │
                                               ◄── Adam optimizer ─┘
```

- Stochastic Opacity Masking (avoids local optima)
- Output: Triangle Soup < 5,000 triangles

### Output
- `output/<subject>_face.obj` — 3D face model
- Eval metrics: PSNR, SSIM, LPIPS vs DiffSoup baseline

---

## Track B — JawTrack Pipeline (Marker-Based)

### ⚠️ Marker Protocol (MANDATORY — all steps in order)

```
Step 1: Attach Fiducial Dot Markers to BOTH upper and lower teeth
Step 2: Confirm markers are firmly attached and visible
Step 3: Perform Intraoral Scan (SHINING 3D) WITH markers in place
Step 4: Verify scan captures all marker positions clearly
Step 5: EXPORT scan (STL/OBJ) — marker 3D positions now in dental frame
Step 6: Keep markers attached for iPhone TrueDepth session
```

**NEVER remove markers before completing Steps 3–4.**

### Step B1 — Intraoral Scan WITH Markers

```
Markers on teeth ──► SHINING 3D Scanner ──► Intraoral Scan (STL/OBJ)
                                                   │
                                      Contains 3D positions of each marker
                                      in the Dental Coordinate Frame
```

### Step B2 — iPhone TrueDepth Capture

```
Patient moving jaw ──► iPhone TrueDepth ──┬─► RGB frames (H × W × 3)
                                           └─► Depth maps (H × W, meters)
                        Camera intrinsics: fx, fy, cx, cy (from ARKit)
```

### Step B3 — Marker Detection & 3D Localization

```
RGB Frame ──► Color/Circle Detection ──► 2D pixel location (u, v)
                                                │
Depth Map + Camera Intrinsics ──► Back-Project ─┘
                                        │
                                 3D point in Camera Frame:
                                 X = (u - cx) * depth / fx
                                 Y = (v - cy) * depth / fy
                                 Z = depth
```

### Step B4 — Scale Verification

```
Marker positions (Camera Frame) ──► Inter-marker distances
                                              │
Marker positions (Dental Frame)  ──► Inter-marker distances
                                              │
                                   Δdistance must be ≤ 0.1 mm
                                   ✅ Pass → proceed
                                   ❌ Fail → re-calibrate / re-scan
```

This verification is possible because intraoral scanners capture absolute scale inherently — no scale ambiguity.

### Step B5 — 6DOF Rigid Body Estimation (SVD)

```
Correspondences: {p_i} in Dental Frame ↔ {q_i} in Camera Frame

  p̄ = mean({p_i}),  q̄ = mean({q_i})
  H = Σ (p_i - p̄)(q_i - q̄)ᵀ
  H = U·Σ·Vᵀ  (SVD)
  R = V·Uᵀ
  t = q̄ - R·p̄

  T = [R | t]   (4×4 transformation matrix per frame)
       [0 | 1]
```

- Applied per-frame → 6DOF jaw motion trajectory

### Output
- `output/<subject>_jaw_motion.json` — list of 4×4 matrices at timestamps
- Eval: RMSE ≤ 0.5 mm vs reference system; fps ≥ 30

---

## Track C — Integration

### Step C1 — Registration (Face ↔ Dental Frame)

```
Marker positions from Intraoral Scan (Dental Frame)
    + Camera calibration from TrueDepth
    + Zero Jaw Position (from Team 1 API)
           │
           ▼
   Rigid alignment of:
     Face Model (Track A) coordinates
     Intraoral Scan coordinates
     6DOF motion trajectory
           │
           ▼
   Everything in single Dental Coordinate Frame
```

### Step C2 — CI-TRANSFORM Export

```json
{
  "version": "1.0",
  "timestamp": "ISO8601",
  "patient_id": "<AES-256 encrypted>",
  "calibration_scale": 1.0,
  "jaw_pose_sequence": [
    {
      "frame": 0,
      "t_ms": 0,
      "T": [[r00,r01,r02,tx],[r10,r11,r12,ty],[r20,r21,r22,tz],[0,0,0,1]]
    }
  ],
  "coordinate_frame": "dental",
  "zero_jaw_position": "<from Team 1 API>"
}
```

### Output
- `output/<subject>_ci_transform.json` (or `.xml`)
- Tested import into Exocad + Team 1 API endpoint

---

## Data Flow Diagram

```
CLINIC SESSION
═══════════════════════════════════════════════════════════════

1. Attach Fiducial Dot Markers to teeth

2. Intraoral Scan (SHINING 3D) ──────────────► dental_scan_WITH_markers.stl
   [Markers MUST be visible in scan]              ↑
                                         Contains 3D marker positions
                                         in Dental Coordinate Frame

3. Multi-view Face Photos (≥40) ─────────────► face_photos/
   [Full face, extra-oral, while smiling]

4. iPhone TrueDepth video ───────────────────► jaw_motion_rgb.mp4
   [Patient opens/closes jaw]                    jaw_motion_depth.bin

═══════════════════════════════════════════════════════════════
PROCESSING (offline)

face_photos/ ──► COLMAP ──► curvature_density.py ──► DiffSoup ──► face_model.obj

dental_scan_WITH_markers.stl ──► extract marker positions (Dental Frame)
jaw_motion_*.* ──► detect markers ──► back-project ──► SVD 6DOF ──► T_jaw(t)

face_model.obj + T_jaw(t) ──► Register ──► CI-TRANSFORM ──► Exocad / Team 1

═══════════════════════════════════════════════════════════════
```

---

## Module Map

```
src/
├── curvature_density.py   [S1 ✅] Principal curvatures + QEM + Density Map
├── colmap_runner.py        [S2]   COLMAP wrapper → Camera poses + point cloud
├── cg_soup_init.py         [S2]   Density-guided Triangle Soup initialization
├── diffsoup_pipeline.py    [S2]   DiffSoup optimization loop (PyTorch)
├── marker_detector.py      [S4]   Detect Fiducial Dots in RGB frames
├── marker_localizer.py     [S4]   Back-project 2D → 3D using TrueDepth depth
├── scale_verify.py         [S4]   Cross-check inter-marker distances ±0.1 mm
├── jaw_tracker.py          [S5]   SVD-based 6DOF per frame
├── registration.py         [S5]   Align face model + jaw motion to dental frame
└── ci_transform_export.py  [S6]   Serialize to CI-TRANSFORM JSON/XML

docs/
├── ARCHITECTURE.md         [S0 ✅] This document
├── แจ้งขอบเขตใหม่_อาจารย์-Team1.md  Scope notification to advisor + Team 1
└── API_Contract_Team1.md   [S5]   API spec for Team 1 integration

data/
├── max-planck.obj          Demo mesh (S1 validation)
└── igea.obj                Demo mesh (S1 validation)
```

---

## Critical Dependencies

| Blocker | Needed For | Status |
|---|---|---|
| Intraoral Scan WITH Markers | All of Track B | ⚠️ Verify if today's scan had markers |
| Multi-view Face Photos | Track A | ❌ Not collected yet |
| Zero Jaw Position from Team 1 API | Track C Registration | ❌ Need API contract |
| Team 1 CI-TRANSFORM Spec | Track C Export | ❌ Need by S5 start |

---

## Tech Stack

| Component | Technology |
|---|---|
| Face Reconstruction | DiffSoup (PyTorch), COLMAP |
| Curvature Analysis | NumPy, SciPy, Open3D |
| iOS Capture | ARKit, AVFoundation, Vision (Swift) |
| Marker Detection | OpenCV (Python) |
| 6DOF Estimation | NumPy SVD |
| CI-TRANSFORM | Python json/xml.etree |
| Data Format | STL/OBJ (mesh), JSON/XML (transforms), PLY (debug) |
| PDPA | AES-256 encryption, raw data deletion post-processing |
