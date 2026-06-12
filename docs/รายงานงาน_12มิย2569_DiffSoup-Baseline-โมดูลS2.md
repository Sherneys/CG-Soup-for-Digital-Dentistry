# รายงานการทำงาน — 12 มิ.ย. 2569: ติดตั้ง DiffSoup + รัน Baseline + โมดูล S2 (Curvature-Guided Init)

> Sprint S1 (W2–3) — โครงการ CG-Soup (ทั้งหน้า) + Jaw Tracking

## สรุปย่อ

วันเดียวปิด 3 งานใหญ่: (1) **build DiffSoup สำเร็จบน Windows** พร้อม smoke test ผ่าน (2) **เปิดรัน baseline เต็ม 10,000 steps** ที่ความละเอียดเต็มกับ buddha scene — กำลังรันอยู่ คาดเสร็จคืนนี้ (3) **เขียนโมดูล S2 (curvature-guided initialization) เสร็จ** ล้ำ roadmap ไป 2 สัปดาห์ — เนื้องานหลักของนวัตกรรม CG-Soup เขียนและทดสอบ sampling ผ่านแล้ว เหลือแค่รอ GPU ว่างเพื่อรันเทียบ

---

## 1. ติดตั้ง/Build DiffSoup บน Windows

- Clone repo ไว้ที่ `D:\Project\diffsoup` build เข้า `.venv` ของโปรเจกต์สำเร็จ
- ต้องใช้ workaround 3 จุด (Ninja generator / `-allow-unsupported-compiler` / `-D__restrict__=__restrict`) — สูตรเต็มบันทึกใน `docs/DiffSoup_การใช้งานในโปรเจกต์.md`
- **Smoke test 200 steps ผ่านครบทุกขั้น** (training, resample, checkpoint, test eval) ใช้เวลา ~10 นาที
- **จุดเชื่อมกับ pipeline เราตรงตามคาด:** `--scene_root output\buddha_sfm\dense` ใช้ output ของ `sfm_pipeline.py` ได้โดยไม่ต้องแปลงอะไรเลย

## 2. DiffSoup Baseline เต็มรูปแบบ (กำลังรัน ⏳)

| รายการ | ค่า |
|---|---|
| คำสั่ง | `01_mip360.py --downscale 1 --batch_size 2` (random init, 10,000 steps) |
| ความละเอียด | 2000×1125 (เต็ม) |
| เริ่มรัน | 05:20 น. |
| คาดเสร็จ | ~18:00–22:00 น. (มี monitor เฝ้า + แจ้งเตือนอัตโนมัติ) |
| Output | `output/diffsoup_buddha_baseline/` → PSNR/SSIM ใน `test_views/metrics.txt` |

**บทเรียนสำคัญที่ได้วันนี้:**

1. **Full res (downscale 1) ใช้เวลา 12–18 ชม.** — ~3.1 วินาที/step ช่วงต้น และหนักขึ้นเรื่อย ๆ (faces โตถึง 15,000 + multi-res lift ที่ step 5,000) → รอบ iterate ต่อไปใช้ `--downscale 4` (ค่า default ของ repo, เร็วขึ้น ~16 เท่า, จบ <1 ชม.) เก็บ full res ไว้รอบ showcase เท่านั้น
2. **สคริปต์ไม่เขียน checkpoint กลางทาง** — ระหว่างรันห้าม kill เด็ดขาด (เสียงานทั้งหมด) ความคืบหน้าดูได้จาก tqdm bar ใน console เท่านั้น
3. VRAM ใช้ 11.8/12.3 GB (96%) — full res + batch 2 ชนเพดาน 4070 Ti พอดี มีความเสี่ยง OOM เล็กน้อยช่วงท้าย

## 3. โมดูล S2: Curvature-Guided Initialization (ไฟล์ใหม่ 2 ไฟล์)

> เนื้องาน Sprint S2 ตาม roadmap (W4–5) — เสร็จล่วงหน้าใน W2 เพราะเป็นงาน CPU ทำคู่ขนานระหว่าง GPU train ได้

### `src/curvature_init.py` — สร้างจุดตั้งต้นตาม density

- โหลด coarse mesh → คำนวณ density map ด้วยฟังก์ชันจาก S1 (`curvature_density.py`) โดยตรง
- Sample จุดบนผิว mesh ด้วยความน่าจะเป็น ∝ พื้นที่ × (floor + density) — `--floor 0.05` กันโซนแบนไม่ให้ไร้จุด
- **ขนาดสามเหลี่ยมต่อจุด** จาก k-NN spacing ในพื้นที่: โซนโค้ง (จุดถี่) ได้สามเหลี่ยมเล็ก โซนแบนได้ใหญ่ — ต่างจากต้นฉบับที่ใช้ scale เดียวทั้ง scene
- Output: `.npz` (points/scales/density) + preview PLY/PNG

### `src/diffsoup_train.py` — training script สลับ init ได้

- สำเนา `01_mip360.py` เพิ่ม `--init {random,curvature}`, `--init_npz`, `--max_faces`
- **ลูป training/loss/resample เหมือนต้นฉบับทุกบรรทัด** — ตัวแปรเดียวที่ต่างคือจุดตั้งต้น เพื่อให้การเทียบ KPI ใน S3 แฟร์
- Verify แล้วว่าสูตร per-point scale ตรงกับ layout ภายในของ `ds.triangle_soup_from_points` (vertex เรียงกลุ่มละ 3, centroid = จุด input)

### ผลทดสอบกับ buddha (CPU ล้วน — รันคู่ขนานกับ baseline ได้)

| รายการ | ค่า |
|---|---|
| Input mesh | `mesh_coarse.ply` (89,258 verts / 170,987 faces) |
| Seeds | 15,000 จุด |
| Density ที่จุด | min 0.000 / median 0.447 / max 1.000 |
| Triangle scale | 0.0037–0.017 (**ต่างกัน ~4.5 เท่า** ระหว่างโซนโค้ง/แบน) |
| Verify ด้วยตา | seeds เกาะหนาแน่นตามขอบ/รายละเอียดพระพุทธรูป เบาบางบนพื้นเรียบ ✅ (`output/mesh_coarse_curv_init_scatter.png`) |

## 4. ระบบ monitor การ train

- ตั้ง monitor เฝ้าโปรเซส baseline — แจ้งเตือนอัตโนมัติเมื่อเสร็จ (พร้อมผล PSNR/SSIM) หรือ crash (แยกกรณีได้ว่า checkpoint รอดไหม)
- บทเรียน: เช็คโปรเซสด้วย `ps` ใน Git Bash บน Windows รวนเป็นครั้งคราว (false alarm 1 ครั้ง) → เปลี่ยนเป็น `tasklist` + ต้องพลาด 4 ครั้งติดถึงนับว่าจบจริง

---

## งานถัดไป

1. **คืนนี้ (พอ baseline เสร็จ):** รันเทียบคู่แรก `--init random` vs `--init curvature` ที่ `--downscale 4`, budget 15,000 faces เท่ากัน → PSNR/SSIM เทียบกันตรง ๆ (คำสั่งพร้อมใช้ใน `docs/DiffSoup_การใช้งานในโปรเจกต์.md`)
2. ทดลองลด `--max_faces` ลงเป็นขั้น ๆ (15,000 → 10,000 → 5,000) ดูว่า curvature-guided ชนะชัดขึ้นไหมเมื่อ budget ตึง (สมมติฐานหลักของโครงการ)
3. **ตัดสินใจวันนี้: ปิด S1 โดยใช้ buddha แทนหน้าจริงไปก่อน** — ชุด A (ภาพหน้าคนจริง) เลื่อนเป็น "เมื่อพร้อม" ไม่ block S2/S3 เพราะทุกโมดูลรับ input ผ่าน argument เสียบข้อมูลจริงได้ทันที
4. งานนอกเครื่องที่ค้าง: ส่งข้อความแจ้งขอบเขตให้อาจารย์/Team 1 (`docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md`)

## ไฟล์ที่เพิ่ม/แก้วันนี้

| ไฟล์ | สถานะ |
|---|---|
| `src/curvature_init.py` | ใหม่ — โมดูล S2: density-weighted sampling + per-point scales |
| `src/diffsoup_train.py` | ใหม่ — DiffSoup training สลับ `--init random\|curvature` |
| `docs/DiffSoup_การใช้งานในโปรเจกต์.md` | ใหม่ — สูตรติดตั้ง/build + วิธีใช้ + สถานะ |
| `output/mesh_coarse_curv_init.npz` | ใหม่ — seeds 15,000 จุดของ buddha |
| `output/mesh_coarse_curv_init_preview.ply` / `_scatter.png` | ใหม่ — visualization สำหรับ verify |
| `output/diffsoup_buddha_smoke/` | ใหม่ — ผล smoke test 200 steps |
| `output/diffsoup_buddha_baseline/` | กำลังสร้าง — baseline 10,000 steps (เสร็จคืนนี้) |
| `plan.md` | อัปเดต — สถานะ S2 ล้ำแผน + งานถัดไป |
