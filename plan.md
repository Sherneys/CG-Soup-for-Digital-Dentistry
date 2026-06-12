# Plan — CG-Soup (ใบหน้าทั้งหน้า) + JawTrack (Marker-Based)

> แผนทำงานปัจจุบัน อัปเดต 12 มิ.ย. 2569 (สัปดาห์ที่ 2 — **S1 ปิดแล้วโดยใช้ buddha dataset แทนหน้าจริงไปก่อน** / เนื้องาน S2 เสร็จล่วงหน้า)

---

## ขอบเขตโครงการ (Confirmed Scope)

| Track | สิ่งที่สร้าง | วิธี |
|---|---|---|
| **Track A — CG-Soup** | โมเดล 3D **ใบหน้าทั้งหน้า** (extra-oral) < 5,000 สามเหลี่ยม | ภาพหลายมุม → SfM → Curvature-Guided DiffSoup |
| **Track B — JawTrack** | การเคลื่อนไหวขากรรไกร 6DOF | Fiducial Dot Markers บนฟัน + Intraoral Scan + iPhone TrueDepth |
| **Track C — Integration** | CI-TRANSFORM (JSON/XML) เข้า Exocad / Team 1 | Registration หน้า ↔ ฟัน + Marker Anchor |

### ขอบเขตของแต่ละ Track ที่ชัดเจน

**Track A (CG-Soup = ใบหน้า ไม่ใช่ฟัน):**
- บริเวณโค้งสูง → สามเหลี่ยมถี่: **จมูก ริมฝีปาก หู ขอบตา คาง**
- บริเวณราบ → สามเหลี่ยมห่าง: **แก้ม หน้าผาก**
- ข้อมูลฟัน/เหงือก = มาจาก Intraoral Scan เท่านั้น (ไม่ใช่จาก CG-Soup)
- ต้องเก็บชุดภาพ "ยิ้มเห็นฟัน" 1 ชุดเพิ่ม สำหรับใช้เป็นสะพานตอน registration

**Track B (JawTrack = Marker-Based ไม่ใช่ FreeMoCap skeleton):**
- ติด Fiducial Dot Markers บนฟันบน + ล่าง (ดูภาพอ้างอิง)
- **Intraoral Scan ต้องทำขณะ Marker ติดอยู่** → ได้ตำแหน่ง 3D ของ Marker ในกรอบพิกัดฟัน
- iPhone TrueDepth ตรวจจับ Marker จากภายนอก → Back-Project → ตำแหน่ง 3D ต่อ Frame
- SVD-based Rigid Body → 6DOF Transformation Matrix ต่อ Frame
- Scale = ใช้ระยะห่างระหว่าง Marker จาก Intraoral Scan (ไม่มี Scale Ambiguity)

---

## ⚠️ Marker Protocol (บังคับทุก Session)

1. **ติด Fiducial Dot Markers** บนฟันบน + ล่าง
2. **Intraoral Scan WITH Markers** (SHINING 3D) → STL/OBJ มีตำแหน่ง Marker
3. **ตรวจสอบ** ว่า Marker ปรากฏครบใน STL/OBJ → ถ้าขาดต้องสแกนใหม่
4. **iPhone TrueDepth** บันทึกการเคลื่อนไหวขากรรไกร
5. **ถอด Marker** ได้หลังจาก ข้อ 2–4 ยืนยันสำเร็จแล้วเท่านั้น

> 🔴 ข้อมูลจากคลินิกวันแรก: ตรวจสอบว่า Intraoral Scan มี Marker ติดอยู่ขณะสแกนหรือไม่
> ถ้าไม่มี → ต้องนัดสแกนใหม่ก่อนเริ่ม Sprint S4

---

## สถานะตอนนี้ (Sprint S1: 8–21 มิ.ย.) — ✅ ปิดแล้ว 12 มิ.ย.

> **ตัดสินใจ 12 มิ.ย.:** S1 ปิดโดยใช้ **buddha dataset แทนหน้าคนจริงไปก่อน** — pipeline/โมดูลครบและ verify ผ่านหมดแล้ว การรันซ้ำกับภาพหน้าจริง (ชุด A) เป็นงานติดตามผลเมื่อได้ข้อมูล **ไม่ block S2/S3** (ทุกโมดูลรับ input ผ่าน argument อยู่แล้ว เสียบชุด A ได้ทันทีโดยไม่ต้องแก้โค้ด)

สิ่งที่เปลี่ยนเพราะขอบเขตใหม่:
- [x] Input ของโมดูล = coarse mesh **ของหน้า** (จาก SfM/COLMAP บนภาพหน้า หรือ TrueDepth depth) — ✅ pipeline E2E ผ่านแล้ว (11 มิ.ย.): `src/sfm_pipeline.py` รัน COLMAP CUDA ครบ feature→match→sparse→dense→Poisson บนชุด buddha head 67 ภาพ ([alicevision/dataset_buddha](https://github.com/alicevision/dataset_buddha)) → simplify เป็น 89k vertices → density map ร้อนที่รายละเอียดหน้า เย็นที่ฉากหลัง (`output/mesh_coarse_density.png`) — **ใช้ buddha เป็นตัวแทนหน้าจริงไปก่อน (ปิด S1)** รันซ้ำกับชุด A เมื่อได้ข้อมูล
- [x] Verify ใหม่: visualize density map แล้วบริเวณ **จมูก ริมฝีปาก หู ขอบตา** ต้อง "ร้อน" (หนาแน่นสูง) ส่วนแก้ม/หน้าผากต้องเย็น — ✅ ผ่านบน max-planck + igea (ดู `output/*_density.png`)
- [x] ถ้ายังไม่มีข้อมูลหน้าจริง ใช้ mesh หน้าสาธารณะไปก่อน (เช่น FaceScape sample, หัว mannequin สแกน) — อย่ารอข้อมูลคลินิก — ✅ ใช้ max-planck.obj + igea.obj ใน `data/`

### งานที่ทำล้ำ roadmap ไปแล้ว (12 มิ.ย.)

- [x] **DiffSoup ติดตั้ง/build สำเร็จบน Windows** เข้า `.venv` (สูตร + workaround 3 จุดบันทึกใน `docs/DiffSoup_การใช้งานในโปรเจกต์.md`)
- [x] **Smoke test 200 steps ผ่าน** กับ buddha scene — ยืนยัน output ของ `sfm_pipeline.py` ป้อนเข้า `01_mip360.py` ได้ตรง ๆ
- [⏳] **DiffSoup baseline เต็ม 10,000 steps (full res, random init) กำลังรัน** — เริ่ม 05:20 น. 12 มิ.ย. คาดเสร็จ ~18:00–22:00 น. (บทเรียน: full res ใช้ 12–18 ชม. รอบ iterate ต่อไปใช้ `--downscale 4` จบ <1 ชม.) → ผลคือตัวเลขฝั่ง random init ของ KPI S3
- [x] **โมดูล S2 (curvature-guided init) เขียนเสร็จ + ทดสอบ sampling ผ่าน** (เนื้องาน Sprint S2 ตาม roadmap):
  - `src/curvature_init.py` — density map → seeds 15,000 จุด + per-point triangle scale (โซนโค้งได้สามเหลี่ยมเล็ก/ถี่ ต่างกัน ~4.5 เท่า) verify ด้วยตาบน buddha แล้ว
  - `src/diffsoup_train.py` — training script ที่สลับ `--init random|curvature` ได้ ลูปเหมือนต้นฉบับทุกบรรทัดเพื่อเทียบแฟร์
- [ ] **เหลือของ S2:** รัน `--init curvature` E2E ครั้งแรก (รอ GPU ว่างจาก baseline) + ทดลองลด budget ลงสู่เป้า <5,000 สามเหลี่ยม

---

## เช็คลิสต์เก็บข้อมูลที่คลินิก

### ชุด A — ภาพหลายมุมของหน้า (input หลักของ CG-Soup)
- [ ] กวาดรอบหน้า ~180° (หูซ้าย → หน้าตรง → หูขวา) แถวบน-กลาง-ล่าง รวม **≥ 40–80 ภาพ**
- [ ] ครอบคลุมหน้าผากถึงใต้คาง **รวมหูทั้งสองข้าง**
- [ ] ปิดปากสบาย ๆ สีหน้า neutral **ห้ามขยับระหว่างกวาด** (SfM พัง)
- [ ] เก็บผม เอาแว่น แสงสม่ำเสมอ ปิด beauty filter ล็อก exposure/focus
- [ ] **เพิ่ม 1 ชุด "ยิ้มเห็นฟัน"** — ไว้เชื่อมหน้า ↔ ฟันตอน registration

### ชุด B — ข้อมูลขากรรไกร (Track B, ตั้งแต่ S4)
- [ ] **ติด Fiducial Dot Markers ก่อน** ทุกอย่าง
- [ ] Intraoral Scan (SHINING 3D) **ขณะ Marker ติดอยู่** → STL บน+ล่าง
- [ ] ตรวจสอบ Marker ครบใน STL ก่อนถอด
- [ ] วิดีโอ iPhone TrueDepth: อ้า-หุบ, ยื่นคาง, เยื้องซ้าย-ขวา อย่างละ ~3 รอบ

### ชุด C — ข้อมูลอ้างอิง
- [ ] Intraoral scan bite (ท่าสบฟัน) — สำหรับ Zero Jaw Position
- [ ] CBCT DICOM (ถ้ามีและได้รับอนุญาต)
- [ ] จด: รุ่น IOS, รุ่น CBCT, เวอร์ชัน Exocad, รูปแบบ import ที่รับได้

---

## Timeline (14 สัปดาห์)

| Sprint | สัปดาห์ | งานหลัก | Deliverable |
|---|---|---|---|
| ~~S0~~ | ~~W1~~ | ~~ตั้ง env, ศึกษา DiffSoup/FreeMoCap, เตรียม SfM~~ | ✅ ควรเสร็จแล้ว — ถ้ายัง ให้ปิดให้จบใน W2 |
| ~~S1~~ | W2–3 (ถึง 21 มิ.ย.) | ~~Curvature analysis + QEM บน mesh~~ | ✅ ปิดแล้ว 12 มิ.ย. — verify บน buddha (ตัวแทนหน้าจริง) + mesh สาธารณะ 2 ชุด |
| S2 🏃 ล้ำแผน | W4–5 | Curvature-guided init + ต่อ DiffSoup pipeline | โมเดลหน้า CG-Soup <5,000 สามเหลี่ยม — **โค้ดเสร็จแล้ว 12 มิ.ย. (W2)** เหลือรัน E2E + ลด budget |
| S3 | W6 | Regularization loss + วัด PSNR/SSIM/LPIPS เทียบ DiffSoup baseline | รายงานผลโมเดล 3D — baseline ฝั่ง random กำลังรันอยู่ |
| S4 | W7–8 | Jaw tracking 6DOF: Marker Detection + 3D Localization + Scale Verify (TrueDepth) | สคริปต์ตรวจจับ Marker + ผล Scale |
| S5 | W9–10 | Registration: motion ↔ โมเดลหน้า ↔ intraoral scan (Zero Jaw Position กับ Team 1) | โค้ด transformation matrix |
| S6 | W11 | Exporter CI-TRANSFORM (JSON/XML) → API Team 1 / Exocad | การเชื่อมต่อสำเร็จ |
| S7 | W12–13 | ทดสอบอาสาสมัคร ≥10 คน: RMSE ≤ 0.5 มม., ≥ 30 fps | รายงานเปรียบเทียบความแม่นยำ |
| S8 | W14 | จูน performance, รายงานฉบับสมบูรณ์, demo video | ส่งมอบครบ |

---

## งานที่ต้องทำทันที (สัปดาห์นี้)

1. เก็บข้อมูลชุด A ที่คลินิก ตามเช็คลิสต์ข้างบน → **เลื่อนเป็น "เมื่อพร้อม" ไม่ block งานพัฒนา** (ตัดสินใจ 12 มิ.ย.: ใช้ buddha แทนไปก่อนทุก sprint จนกว่าจะได้ข้อมูลจริง)
2. รัน COLMAP + curvature + DiffSoup ซ้ำกับภาพชุด A เมื่อได้ข้อมูล → 🔧 เครื่องมือพร้อมหมดแล้ว เสียบโฟลเดอร์ภาพแล้วรันได้เลยทั้งเส้น (`sfm_pipeline.py` → `curvature_init.py` → `diffsoup_train.py`)
3. ~~เริ่มโมดูล curvature: principal curvatures + QEM ต่อ vertex บน mesh หน้า~~ ✅ เสร็จแล้ว (11 มิ.ย.) — `src/curvature_density.py` verify ผ่านบน mesh สาธารณะ 2 ชุด เหลือรันซ้ำกับ mesh หน้าจริงเมื่อได้ข้อมูลชุด A
4. **แจ้งอาจารย์/Team 1 เรื่องขอบเขต "ทั้งหน้า ไม่ใช่ฟัน"** ให้เป็นลายลักษณ์อักษร แล้วแก้ข้อเสนอโครงการ — กัน KPI/การตรวจรับเพี้ยนตอนท้ายเทอม → ✅ ข้อเสนอโครงการแก้เป็น "ใบหน้า" ทั้งฉบับแล้ว (11 มิ.ย.) / 📝 ร่างข้อความแจ้งพร้อมส่งที่ `docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md` (**ยังไม่ได้ส่ง — ต้องส่งเอง**)
5. เปิดคุย API contract กับ Team 1 เรื่อง landmark / Zero Jaw Position ตั้งแต่ตอนนี้ (roadmap เตือนว่าอย่ารอถึง S5) → 📝 รายการประเด็น 6 ข้อร่างไว้ใน `docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md` ส่วนที่ 2
6. **พอ baseline เสร็จ (คืนนี้):** รันเทียบ random vs curvature ที่ `--downscale 4` (คำสั่งพร้อมใช้ใน `docs/DiffSoup_การใช้งานในโปรเจกต์.md`) — ได้ตัวเลข PSNR/SSIM เทียบกันคู่แรกของโครงการ

---

## ความเสี่ยง

| ความเสี่ยง | แนวทางรับมือ |
|---|---|
| Intraoral Scan ไม่มี Marker (ข้อมูลวันแรก) | นัดสแกนใหม่ WITH Markers — Track B หยุดถ้าไม่มีข้อมูลนี้ |
| Marker หลุด/เลื่อนระหว่าง Session | ตรวจสอบก่อน/หลัง; ถ้าเลื่อนต้องสแกนใหม่ |
| iPhone ตรวจจับ Marker ไม่ได้ | กำหนดโปรโตคอลแสง; Fallback = ArUco Coded Markers |
| ผิวหน้า non-rigid (หน้าขยับ) | Protocol ถ่ายต้องคุม neutral เข้มงวด |
| API contract กับ Team 1 ล่าช้า | เริ่มคุยตอนนี้ — Block S5 ถ้า Spec ยังไม่นิ่ง |
| เชื่อมหน้า ↔ ฟัน ไม่มี overlap | ใช้ชุดภาพ "ยิ้มเห็นฟัน" หรือ bite jig เป็นสะพาน |
| DiffSoup โค้ดใหม่ปี 2026 | เผื่อ debug time S0–S2 |
| PDPA | เข้ารหัส + ลบข้อมูลดิบตั้งแต่ออกแบบ S6 |
