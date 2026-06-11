# Plan — CG-Soup (ใบหน้าทั้งหน้า) + JawTrack (Marker-Based)

> อัปเดต 11 มิ.ย. 2569 | **Team 4** | รหัสโครงการ CP-2026-A4
> เอกสารนี้คือแผนปฏิบัติงานจริง — ดู `docs/ARCHITECTURE.md` สำหรับ block diagram เต็ม

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

## สถานะปัจจุบัน (Sprint S1: 8–21 มิ.ย. 2569)

| งาน | สถานะ |
|---|---|
| ตั้ง Python env (conda `dent`) + DiffSoup clone | ✅ เสร็จ |
| `src/curvature_density.py` — principal curvatures + QEM + density map | ✅ เสร็จ (11 มิ.ย.) |
| Verify density map บน max-planck + igea (จมูก/ปาก/หู = ร้อน) | ✅ ผ่าน |
| แจ้งขอบเขต "ใบหน้า ไม่ใช่ฟัน" → อาจารย์ + Team 1 | 📝 ร่างพร้อม (ดู `docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md`) — **ยังไม่ส่ง** |
| ถ่ายภาพหน้า multi-view ≥ 40 มุม (ข้อมูลจริง) | ⬜ ยังไม่ได้ทำ |
| รัน COLMAP บนภาพหน้าจริง | ⬜ รอภาพก่อน |
| Verify density map บน mesh หน้าจริง | ⬜ รอ COLMAP |
| เปิดคุย API contract กับ Team 1 | ⬜ ต้องทำเร็ว ๆ นี้ |

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

| Sprint | สัปดาห์ | งานหลัก | Deliverable | สถานะ |
|---|---|---|---|---|
| S0 | W1 1–7 มิ.ย. | ตั้ง env, ศึกษา DiffSoup, Architecture Report | Architecture doc + env setup | ✅ |
| **S1** | **W2–3 8–21 มิ.ย.** | **Curvature Analysis บน mesh หน้า** | **โมดูล + Density Map (จมูก/ปาก/หูร้อน)** | **⬤ กำลังทำ** |
| S2 | W4–5 22 มิ.ย.–5 ก.ค. | CG-Soup Initialization + ต่อ DiffSoup | โมเดลหน้า CG-Soup < 5,000 สามเหลี่ยม | ⬜ |
| S3 | W6 6–12 ก.ค. | Regularization + วัด PSNR/SSIM/LPIPS | รายงานผลโมเดล 3D | ⬜ |
| S4 | W7–8 13–26 ก.ค. | Marker Detection + 3D Localization + Scale Verify | สคริปต์ตรวจจับ Marker + ผล Scale | ⬜ |
| S5 | W9–10 27 ก.ค.–9 ส.ค. | 6DOF Rigid Body + Registration (Dental Frame) | โค้ด Transformation Matrix | ⬜ |
| S6 | W11 10–16 ส.ค. | CI-TRANSFORM Exporter + API Team 1 / Exocad | ส่งออก CI-TRANSFORM สำเร็จ | ⬜ |
| S7 | W12–13 17–30 ส.ค. | ทดสอบอาสาสมัคร ≥ 10 คน: RMSE ≤ 0.5 มม., ≥ 30 fps | รายงานความแม่นยำ | ⬜ |
| S8 | W14 31 ส.ค.–6 ก.ย. | Performance tuning + รายงาน + demo | ส่งมอบครบ | ⬜ |

---

## งานที่ต้องทำทันที (สัปดาห์นี้)

1. **ส่งข้อความแจ้งขอบเขต** → อาจารย์ + Team 1 (ร่างอยู่ใน `docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md`)
2. **ถ่ายภาพหน้า multi-view** ≥ 40 มุม ตามเช็คลิสต์ชุด A (ถ่ายตัวเองได้ก่อน)
3. **รัน COLMAP** → coarse face mesh → รัน `curvature_density.py` บน mesh หน้าจริง
4. **เปิดคุย API contract กับ Team 1** — ประเด็น 6 ข้อใน `docs/แจ้งขอบเขตใหม่_อาจารย์-Team1.md`

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
