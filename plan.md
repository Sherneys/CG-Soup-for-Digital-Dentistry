# Plan — CG-Soup (ทั้งหน้า) + Jaw Tracking

> แผนทำงานปัจจุบัน อัปเดต 12 มิ.ย. 2569 (สัปดาห์ที่ 2 — **S1 ปิดแล้วโดยใช้ buddha dataset แทนหน้าจริงไปก่อน** / เนื้องาน S2 เสร็จล่วงหน้า)

---

## ⚠️ การแก้ขอบเขตสำคัญ (ต่างจากข้อเสนอโครงการ)

**CG-Soup สร้างโมเดล 3D ของ "ใบหน้าทั้งหน้า" (extra-oral) — ไม่ใช่ฟัน**

| หัวข้อ | ข้อเสนอเดิมเขียนว่า | ขอบเขตจริง |
|---|---|---|
| เป้าหมาย CG-Soup | โมเดลฟัน/ช่องปาก | **ใบหน้าทั้งหน้า** |
| บริเวณความโค้งสูง (สามเหลี่ยมถี่) | ปุ่มฟัน ขอบฟัน ขอบครอบฟัน | **จมูก ริมฝีปาก หู ขอบตา คาง** |
| บริเวณราบ (สามเหลี่ยมห่าง) | เหงือก เพดานปาก | **แก้ม หน้าผาก** |
| ข้อมูลฟัน/เหงือก | จาก CG-Soup | **จาก Intraoral Scan (IOS) ของคลินิกเท่านั้น** |

สิ่งที่**ไม่เปลี่ยน**: สถาปัตยกรรม DiffSoup + curvature-guided initialization, เป้า <5,000 สามเหลี่ยม, Jaw Tracking ด้วย iPhone TrueDepth + FreeMoCap, ส่งออก CI-TRANSFORM เข้า Exocad/Team 1

ผลที่ตามมา:
- โมเดลหน้าจาก CG-Soup = พื้นผิวอ้างอิงที่ jaw motion ไปซ้อนทับ และเป็นตัวเชื่อมกับ intraoral scan ตอน registration
- ชุดข้อมูลที่ต้องเก็บคือ **ภาพหลายมุมของหน้า** (ไม่ใช่ในช่องปาก) → ถ่ายง่ายกว่า ไม่ต้องใช้อุปกรณ์ intra-oral
- งบ <5,000 สามเหลี่ยมสำหรับทั้งหน้าโอเค เพราะความโค้งสูงกระจุกที่จมูก/ปาก/หู ส่วนแก้ม/หน้าผากราบมาก — เข้าทาง curvature-guided พอดี
- ต้องนิยาม "ความแม่นยำ" ใหม่: ที่สำคัญคือบริเวณรอบปาก/คาง (โซนที่ขากรรไกรขยับ) ไม่ใช่ผิวฟัน

---

## สถานะตอนนี้ (Sprint S1: 8–21 มิ.ย.) — ✅ ปิดแล้ว 12 มิ.ย.

เป้า S1 ตาม roadmap: **โมดูลวิเคราะห์ความโค้ง (principal curvatures + QEM) + Density Map**

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
- [ ] วิดีโอ/ภาพนิ่งกวาดรอบหน้า ~180° (หูซ้าย → หน้าตรง → หูขวา) แถวบน-กลาง-ล่าง รวม ≥ 40–80 ภาพ
- [ ] ครอบคลุมหน้าผากถึงใต้คาง **รวมหูทั้งสองข้าง** (หูสำคัญต่อ registration กับ CBCT)
- [ ] สีหน้า neutral ปิดปากสบาย ๆ **ห้ามขยับหน้า/หลับตาเปลี่ยนจังหวะระหว่างกวาด** (SfM จะพัง)
- [ ] เก็บผมออกจากหน้าผาก/หู ถอดแว่น แสงสม่ำเสมอ ไม่ย้อนแสง ปิด beauty filter
- [ ] ถ้าใช้ iPhone: ล็อก exposure/focus (กดค้างบนจอ) กันสีเพี้ยนข้ามเฟรม
- [ ] เพิ่มอีก 1 ชุด: ยิ้มเห็นฟัน (ไว้เชื่อมหน้า ↔ ฟันตอน registration)

### ชุด B — ข้อมูลขากรรไกร (Track B, ใช้ตั้งแต่ S4)
- [ ] วิดีโอ TrueDepth ขณะอ้า-หุบปาก, ยื่นคาง, เยื้องซ้าย-ขวา (อย่างละ ~3 รอบ)
- [ ] มีวัตถุขนาดรู้จริงในเฟรมหรือวัด jig ไว้ → ใช้แก้ Scale Ambiguity ของ FreeMoCap

### ชุด C — ข้อมูลอ้างอิงจากคลินิก
- [ ] Intraoral scan (STL/PLY): บน + ล่าง + bite — เป็นกรอบพิกัดอ้างอิงตอน registration
- [ ] CBCT DICOM (ถ้ามีและได้รับอนุญาต) — ไว้ validate ผิวหน้า
- [ ] จด: รุ่น IOS scanner, รุ่น CBCT, เวอร์ชัน Exocad ที่คลินิกใช้, รูปแบบ import ที่ Exocad รับ

### ทุกชุด
- [ ] Consent ตาม PDPA ก่อนถ่าย (ข้อมูลหน้า = ระบุตัวตนได้โดยตรง)
- [ ] ตารางเชื่อมข้อมูล: รหัสอาสาสมัคร ↔ ไฟล์ชุด A/B/C ↔ วันที่ถ่าย
- [ ] เก็บ A+B+C ของคนเดียวกัน **ในวันเดียวกัน**

---

## Timeline (คงตาม roadmap เดิม ปรับเนื้อหาเป็น "หน้า")

| Sprint | สัปดาห์ | งานหลัก | Deliverable |
|---|---|---|---|
| ~~S0~~ | ~~W1~~ | ~~ตั้ง env, ศึกษา DiffSoup/FreeMoCap, เตรียม SfM~~ | ✅ ควรเสร็จแล้ว — ถ้ายัง ให้ปิดให้จบใน W2 |
| ~~S1~~ | W2–3 (ถึง 21 มิ.ย.) | ~~Curvature analysis + QEM บน mesh~~ | ✅ ปิดแล้ว 12 มิ.ย. — verify บน buddha (ตัวแทนหน้าจริง) + mesh สาธารณะ 2 ชุด |
| S2 🏃 ล้ำแผน | W4–5 | Curvature-guided init + ต่อ DiffSoup pipeline | โมเดลหน้า CG-Soup <5,000 สามเหลี่ยม — **โค้ดเสร็จแล้ว 12 มิ.ย. (W2)** เหลือรัน E2E + ลด budget |
| S3 | W6 | Regularization loss + วัด PSNR/SSIM/LPIPS เทียบ DiffSoup baseline | รายงานผลโมเดล 3D — baseline ฝั่ง random กำลังรันอยู่ |
| S4 | W7–8 | Jaw tracking 6DOF (TrueDepth + FreeMoCap) + scale calibration | สคริปต์ motion + ผล calibrate |
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

## ความเสี่ยงเพิ่มเติมจากขอบเขตใหม่

- **ผิวหน้าไม่แข็ง (non-rigid):** หน้าขยับ/แสดงสีหน้าได้ ต่างจากฟัน — protocol ถ่ายต้องคุม neutral เข้มงวด ไม่งั้น SfM/optimization เพี้ยน
- **ผม คิ้ว ขนตา:** triangle soup กับบริเวณเส้นผมไม่เข้ากัน → ตัด scope ที่ "ผิวหน้า" ใช้ hair cap ถ้าจำเป็น
- **ผิวหน้า specular/ผิวมัน:** ทำ color loss เพี้ยน → ระวังแสง ใช้แสงกระจาย (diffuse)
- **เชื่อมหน้า ↔ ฟัน:** หน้า (extra-oral) กับ intraoral scan แทบไม่มีพื้นผิวซ้อนกัน — ต้องใช้ชุด "ยิ้มเห็นฟัน" หรือ bite jig เป็นสะพานตอน registration (จุดนี้ต้องตกลงกับ Team 1 เร็ว ๆ)
- ความเสี่ยงเดิมจาก roadmap ยังอยู่ครบ: Scale Ambiguity, DiffSoup เป็นโค้ดใหม่ปี 2026, PDPA, ตัวเลข KPI ต้องวัดจริง
