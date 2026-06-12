# CG-Soup + JawTrack — Digital Dentistry (CP-2026-A4)

**Team 4** | 14-week intern project | 2026-06-01 → 2026-09-06

ระบบสร้างแบบจำลองใบหน้าสามมิติและติดตามการเคลื่อนไหวขากรรไกรสำหรับงานทันตกรรมดิจิทัล

---

## ภาพรวมโครงการ (Project Overview)

โครงการนี้ประกอบด้วยสองส่วนหลักที่บูรณาการเข้าหากัน:

**Track A — CG-Soup:** ถ่ายภาพใบหน้าทั้งหน้า (extra-oral) หลายมุมขณะยิ้ม → SfM (COLMAP) → วิเคราะห์ความโค้งหลัก (κ₁, κ₂) → CG-Soup Initialization → DiffSoup → แบบจำลอง 3D ใบหน้า < 5,000 สามเหลี่ยม

**Track B — JawTrack:** ติด Fiducial Dot Markers บนฟัน → Intraoral Scan WITH Markers (SHINING 3D) → iPhone TrueDepth ตรวจจับ Markers จากภายนอก → SVD 6DOF ต่อ Frame → ข้อมูลการเคลื่อนไหวขากรรไกร

**Track C — Integration:** Register ข้อมูลทั้งสอง → ส่งออก CI-TRANSFORM (JSON/XML) → Exocad / Team 1 API

---

## ⚠️ Marker Protocol (บังคับ — ห้ามข้าม)

```
1. ติด Fiducial Dot Markers บนฟันบนและฟันล่าง
2. ตรวจสอบว่า Markers ติดแน่น
3. สแกน Intraoral (SHINING 3D) ขณะ Markers ยังติดอยู่
4. ยืนยันว่า Scan เห็น Markers ครบ
5. Export STL/OBJ — ตำแหน่ง 3D ของ Markers อยู่ใน Dental Frame แล้ว
6. คง Markers ไว้สำหรับ iPhone TrueDepth Session
```

**ห้ามถอด Markers ก่อนยืนยันว่า Intraoral Scan สำเร็จ**

---

## โครงสร้างโปรเจค (Repository Structure)

```
.
├── src/
│   ├── curvature_density.py    [S1 ✅] Curvature analysis + QEM + Density Map
│   ├── colmap_runner.py         [S2]   SfM wrapper
│   ├── cg_soup_init.py          [S2]   Triangle Soup initialization
│   ├── diffsoup_pipeline.py     [S2]   DiffSoup optimization
│   ├── marker_detector.py       [S4 ✅ code] Detect markers in RGB frames
│   ├── marker_localizer.py      [S4 ✅ code] Back-project to 3D via TrueDepth
│   ├── scale_verify.py          [S4 ✅ code] Verify inter-marker distances ±0.1mm
│   ├── jaw_tracker.py           [S5 ✅ code] SVD 6DOF per frame
│   ├── registration.py          [S5 ✅ code] Align to dental coordinate frame
│   └── ci_transform_export.py   [S6]   CI-TRANSFORM JSON/XML export
├── data/
│   ├── max-planck.obj           Demo mesh (S1 testing)
│   └── igea.obj                 Demo mesh (S1 testing)
├── docs/
│   ├── ARCHITECTURE.md          System architecture and data flow
│   └── แจ้งขอบเขตใหม่_อาจารย์-Team1.md  Scope notification (draft)
├── output/                      Generated outputs (gitignored for patient data)
├── plan.md                      Sprint plan + current status
├── CG-Soup_Jaw-Tracking_ข้อเสนอโครงการรวม.md  Full project proposal (TH+EN)
└── README.md                    This file
```

---

## การติดตั้ง (Setup)

### Python Environment (Track A)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch torchvision numpy scipy open3d trimesh matplotlib
```

### Test Curvature Module (S1 — already working)

```bash
python src/curvature_density.py data/max-planck.obj --out-dir output/
# Output: output/max-planck_density.ply + output/max-planck_density.png
# Expected: nose/lips/ears/eye rims = hot (red), cheeks/forehead = cool (blue)
```

### Track B — JawTrack Pipeline (code ✅, รอข้อมูลคลินิก)

โค้ดทุกโมดูลเสร็จและผ่าน unit test ด้วยข้อมูลสังเคราะห์แล้ว (Track B ทำคู่ขนานกับ Track A)
เมื่อได้ข้อมูลจริงจากคลินิก รันตามลำดับ:

```bash
pip install -r requirements.txt   # เพิ่ม opencv-python + pytest แล้ว

# B3a: ตรวจจับ marker จากวิดีโอ iPhone (จุดน้ำเงิน = ฟันบน, จุดเขียว = ฟันล่าง — ปรับ HSV ได้ผ่าน --config)
python src/marker_detector.py jaw_motion.mp4 --out output/detections.json

# B3b: Back-project 2D → 3D ด้วย depth map (.npy หน่วยเมตร) + intrinsics จาก ARKit
python src/marker_localizer.py output/detections.json intrinsics.json \
    --depth-dir data/session01/depth --rgb-size 1920 1440 --out output/points3d.json

# B4: ตรวจ scale เทียบ Intraoral Scan (ต้องผ่าน ±0.1 mm ก่อนไปต่อ — exit code 1 ถ้าไม่ผ่าน)
python src/scale_verify.py dental_markers.json output/points3d.json

# B5: 6DOF ต่อ frame (--auto-label จับคู่ marker id อัตโนมัติจากระยะห่างระหว่าง marker)
python src/jaw_tracker.py dental_markers.json output/points3d.json \
    --auto-label --out output/jaw_motion.json

# S5: Registration เข้า dental frame (รองรับ transform mesh ด้วย)
python src/registration.py landmarks_cam.json landmarks_dental.json --out output/transform.json
```

`dental_markers.json` = ตำแหน่ง marker จาก Intraoral Scan (หน่วย mm):
`{"upper": {"U1": [x,y,z], ...}, "lower": {"L1": [x,y,z], ...}}`

### Run Tests (Track B — ไม่ต้องใช้ข้อมูลคลินิก)

```bash
pytest tests/ -v   # 28 tests: synthetic ground-truth (รวม hinge-motion end-to-end, RMSE ≤ 0.5 mm)
```

### COLMAP (Track A — S2)

```bash
# macOS
brew install colmap

# Run SfM on face photos
colmap automatic_reconstructor --workspace_path output/colmap/ --image_path data/face_photos/
```

---

## Sprint Status

| Sprint | สัปดาห์ | เนื้อหา | สถานะ |
|---|---|---|---|
| S0 | W1 | Env + Architecture + Data Collection Planning | ✅ Done |
| S1 | W2–3 | Curvature Module (κ₁,κ₂ + QEM + Density Map) | ✅ Done |
| S2 | W4–5 | CG-Soup Init + DiffSoup Pipeline | 🔲 |
| S3 | W6 | Regularization + Metrics (PSNR/SSIM/LPIPS) | 🔲 |
| S4 | W7–8 | Marker Detection + 3D Localization + Scale Verify | 🟡 Code ✅ (12 มิ.ย. — รอข้อมูลคลินิก) |
| S5 | W9–10 | SVD 6DOF + Registration | 🟡 Code ✅ (12 มิ.ย. — รอข้อมูลคลินิก) |
| S6 | W11 | CI-TRANSFORM Export + Team 1 API + PDPA | 🔲 |
| S7 | W12–13 | User Testing (≥10 volunteers) | 🔲 |
| S8 | W14 | Performance Tuning + Final Demo | 🔲 |

---

## ข้อมูลที่ต้องเก็บ (Data Collection Checklist)

### Track A
- [ ] ภาพถ่ายใบหน้าทั้งหน้า ≥ 40 มุม (extra-oral, ขณะยิ้มเห็นฟัน)
- [ ] ชุด "ยิ้มเห็นฟัน" สำหรับ bridge registration
- [ ] COLMAP reconstruction สำเร็จ

### Track B (**ต้องทำตาม Marker Protocol**)
- [ ] **Intraoral Scan WITH Markers** (SHINING 3D) — ตรวจสอบว่าวันแรกได้ทำหรือยัง
- [ ] วิดีโอ iPhone TrueDepth ขณะเคลื่อนไหวขากรรไกร (jaw open/close/lateral)

### Track C
- [ ] สัญญา API กับ Team 1 (Zero Jaw Position + CI-TRANSFORM spec)

---

## ข้อสำคัญ (Key Points)

- **ขอบเขต Track A:** ใบหน้าทั้งหน้า (extra-oral) — ไม่ใช่ภายในช่องปาก
- **ขอบเขต Track B:** Marker-Based เท่านั้น — ไม่ใช้ FreeMoCap หรือ Software Landmarks
- **Intraoral Scan:** ใช้เป็น Ground-Truth Reference สำหรับ Marker Positions ใน Dental Frame — ไม่ใช่ output ของ Track A
- **Scale:** ไม่มีปัญหา Scale Ambiguity เพราะ Intraoral Scanner มี Absolute Scale ในตัว

---

## เอกสารเพิ่มเติม (Documentation)

- [Architecture Report](docs/ARCHITECTURE.md) — Data flow + module map + critical dependencies
- [Project Proposal](CG-Soup_Jaw-Tracking_ข้อเสนอโครงการรวม.md) — Full proposal (TH+EN)
- [Sprint Plan](plan.md) — Detailed sprint breakdown + risks

---

## อ้างอิง (References)

- [DiffSoup (CVPR 2026)](https://arxiv.org/abs/2603.27151)
- [DiffSoup Code](https://github.com/kenji-tojo/diffsoup)
- [COLMAP](https://colmap.github.io/)
- Apple ARKit / TrueDepth documentation
