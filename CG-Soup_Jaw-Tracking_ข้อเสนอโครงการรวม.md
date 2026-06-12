# ข้อเสนอโครงการวิจัย (Research Project Proposal)

## ระบบสร้างแบบจำลองใบหน้าสามมิติและติดตามการเคลื่อนไหวขากรรไกรด้วยวิธี Curvature-Guided Triangle Soup และ Marker-Based Jaw Tracking สำหรับงานทันตกรรมดิจิทัล

### Curvature-Guided Neural Triangle Soup with Marker-Based Jaw Motion Tracking for Digital Dentistry (CG-Soup + JawTrack)

**รหัสโครงการ:** CP-2026-A4 | **ทีม:** Team 4 | **ที่ปรึกษา:** รศ.ดร.พิษณุ คนองชัยยศ
**ระยะเวลา:** 14 สัปดาห์ (280 ชั่วโมง) เริ่ม 1 มิถุนายน 2569

---

## บทคัดย่อ (Abstract)

งานทันตกรรมดิจิทัล (Digital Dentistry) ต้องการสองสิ่งพร้อมกัน คือ (1) แบบจำลองสามมิติของใบหน้าผู้ป่วยที่มีความถูกต้องเชิงเรขาคณิตสูงและเบาพอใช้งานแบบเรียลไทม์ และ (2) ข้อมูลการเคลื่อนไหวของขากรรไกรที่แม่นยำในหน่วยมิลลิเมตรและองศา โครงการนี้นำเสนอระบบสองส่วน:

**ส่วนที่ 1 — CG-Soup:** ถ่ายภาพใบหน้าทั้งหน้า (extra-oral) หลายมุมขณะยิ้มเห็นฟัน แล้วใช้วิธี Curvature-Guided Neural Triangle Soup ต่อยอดจาก DiffSoup เพื่อสร้างแบบจำลองสามมิติที่ใช้รูปสามเหลี่ยมน้อยกว่า 5,000 ชิ้น โดยการวิเคราะห์ความโค้งหลัก (Principal Curvatures) นำทางการกระจายสามเหลี่ยมให้ถี่ที่บริเวณโค้งสูง (จมูก ริมฝีปาก หู ขอบตา คาง) และห่างบริเวณราบ (แก้ม หน้าผาก)

**ส่วนที่ 2 — JawTrack:** ติด Fiducial Dot Markers บนฟันบนและล่าง แล้วสแกนด้วย Intraoral Scanner (SHINING 3D) ขณะ Marker ยังติดอยู่ เพื่อบันทึกตำแหน่ง 3D ของ Marker แต่ละจุดในกรอบพิกัดฟัน จากนั้นใช้ iPhone TrueDepth บันทึกภาพใบหน้าขณะเคลื่อนไหวขากรรไกร ตรวจจับ Marker จากภายนอก และคำนวณ 6DOF Transformation Matrix ต่อ Frame ด้วยวิธี SVD-based Rigid Body Estimation

ผลลัพธ์ถูกส่งออกในมาตรฐาน CI-TRANSFORM (JSON/XML) เข้าสู่ระบบ Exocad และ API ของ Team 1

---

## 1. ความเป็นมาและความสำคัญของปัญหา (Problem Statement)

การวิเคราะห์การสบฟันและการออกแบบชิ้นงานทันตกรรมต้องอาศัยองค์ประกอบสองส่วนในกรอบพิกัดเดียวกัน ได้แก่ (1) แบบจำลองใบหน้าสามมิติที่ครอบคลุมทั้งบริเวณภายนอกช่องปากและฟัน และ (2) ข้อมูลการเคลื่อนไหวขากรรไกรที่แม่นยำ ระบบดั้งเดิมพึ่งพา Articulator เชิงกลหรืออุปกรณ์ออปติคัลราคาสูง

**ปัญหาที่ 1 — การสร้างแบบจำลอง 3D ใบหน้า:** วิธี DiffSoup สามารถสร้างแบบจำลองจากภาพถ่ายได้ แต่การเริ่มต้นแบบสุ่มทำให้ช้าและสูญเสียรายละเอียดบริเวณความโค้งสูงของใบหน้า (จมูก ริมฝีปาก หู ขอบตา)

**ปัญหาที่ 2 — การติดตามขากรรไกร:** การวัด 6DOF ของขากรรไกรด้วยความแม่นยำ RMSE ≤ 0.5 มม. ต้องอาศัยจุดอ้างอิงที่ตรวจจับได้ทั้งจาก Intraoral Scan และกล้องภายนอก

**วิธีแก้:** ใช้ Fiducial Dot Markers บนฟันเป็น "สะพาน" เชื่อมตำแหน่ง 3D ใน Intraoral Scan กับตำแหน่งที่กล้อง iPhone TrueDepth มองเห็นจากภายนอก ทำให้ Register การเคลื่อนไหวขากรรไกรเข้ากับแบบจำลองใบหน้าได้อย่างแม่นยำโดยไม่มีปัญหา Scale Ambiguity

---

## 2. วัตถุประสงค์ (Objectives)

1. พัฒนาวิธี CG-Soup สำหรับสร้างแบบจำลองสามมิติของใบหน้าทั้งหน้า (extra-oral) จากภาพถ่ายหลายมุมขณะยิ้ม โดยใช้ความโค้งหลักนำทางการเริ่มต้น Triangle Soup ให้ได้แบบจำลองที่ใช้รูปสามเหลี่ยมต่ำกว่า 5,000 ชิ้น
2. พัฒนาระบบ JawTrack ที่ใช้ Fiducial Dot Markers บนฟัน ร่วมกับ Intraoral Scan และ iPhone TrueDepth เพื่อวัดการเคลื่อนไหวขากรรไกร 6DOF ที่มี RMSE ≤ 0.5 มม. และทำงาน ≥ 30 fps
3. บูรณาการสองระบบโดยทำ Registration ข้อมูลการเคลื่อนไหวซ้อนทับบนแบบจำลองใบหน้า CG-Soup / Intraoral Scan และส่งออก CI-TRANSFORM (JSON/XML) เข้าสู่ Exocad
4. ประเมินประสิทธิภาพด้วยเมตริก PSNR/SSIM/LPIPS (Track A) และ RMSE/fps (Track B) จากอาสาสมัคร ≥ 10 คน

---

## 3. ขอบเขตงาน (Scope of Work)

**Track A — CG-Soup (ใบหน้า extra-oral):**
สร้างแบบจำลองสามมิติของใบหน้าทั้งหน้าจากภาพถ่ายหลายมุมขณะยิ้ม โดยใช้ Principal Curvatures นำทางการ Initialize Triangle Soup บริเวณโค้งสูง (จมูก ริมฝีปาก หู ขอบตา คาง) ก่อนเข้าสู่ Differentiable Optimization ของ DiffSoup

**Track B — JawTrack (Marker-Based):**
ติด Fiducial Dot Markers บนฟัน → Intraoral Scan WITH Markers → iPhone TrueDepth ตรวจจับ Marker → SVD-based 6DOF → Registration เข้า Dental Coordinate Frame

**Track C — Integration:**
Register ข้อมูล 6DOF ซ้อนบนแบบจำลอง CG-Soup/Intraoral Scan → ส่งออก CI-TRANSFORM → Exocad / Team 1 API ตาม PDPA

---

## 4. ข้อกำหนดข้อมูลเข้าและผลลัพธ์ (Input / Output Specifications)

### ข้อมูลเข้า (Input)

**Track A:**
- ภาพถ่ายใบหน้าทั้งหน้า (extra-oral) หลายมุมขณะยิ้ม ≥ 40–80 มุม พร้อม Camera Poses จาก SfM (COLMAP)
- ชุดภาพ "ยิ้มเห็นฟัน" เพิ่มอีก 1 ชุด สำหรับสะพาน registration หน้า ↔ ฟัน
- Intraoral Scan (STL/OBJ) — Ground-Truth Reference สำหรับประเมินผล

**Track B:**
- Fiducial Dot Markers ติดบนฟันบนและล่าง (**ต้องติดก่อนสแกนทุกครั้ง**)
- Intraoral Scan WITH Markers in place (STL/OBJ) — ตำแหน่ง 3D ของ Marker ในกรอบพิกัดฟัน
- วิดีโอ iPhone TrueDepth ขณะผู้ป่วยเคลื่อนไหวขากรรไกร

### ผลลัพธ์ (Output)

- แบบจำลองสามมิติใบหน้า (3D Face Model) — Triangle Soup < 5,000 ชิ้น
- ภาพสังเคราะห์มุมมองใหม่ (Novel View Synthesis) — เรนเดอร์ความละเอียดสูง
- ข้อมูล 6DOF Jaw Motion — Transformation Matrix (4×4) ต่อ Frame
- CI-TRANSFORM (JSON/XML) — Timestamp + Calibration Scale + Encrypted Patient ID

---

## 5. ระเบียบวิธี (Methodology)

### ส่วน A — CG-Soup

**A1 — SfM:** ถ่ายภาพใบหน้าหลายมุม → COLMAP → Camera Poses + Coarse Point Cloud

**A2 — Curvature Analysis:** Coarse Mesh → Principal Curvatures (κ₁, κ₂) + QEM ต่อ Vertex → Density Map (โค้งสูง = หนาแน่น)

**A3 — CG-Soup Initialization:** Density Map → Triangle Placement (ถี่บริเวณ จมูก/ปาก/หู, ห่างบริเวณ แก้ม/หน้าผาก)

**A4 — DiffSoup Optimization:** Stochastic Opacity Masking + Differentiable Rasterization + Regularization Loss (Angular/Dihedral/Color/Edge-Gradient)

### ส่วน B — JawTrack

**B1 — Marker Attachment:** ติด Fiducial Dot Markers บนฟันบน + ล่าง

**B2 — Intraoral Scan WITH Markers:** SHINING 3D → STL/OBJ ที่มีตำแหน่ง 3D ของ Marker ในกรอบพิกัดฟัน

**B3 — iPhone TrueDepth Capture:** บันทึก RGB + Depth Map ต่อ Frame ขณะผู้ป่วยขยับขากรรไกร

**B4 — Marker Detection & 3D Localization:** ตรวจจับ Marker ในภาพ RGB → Back-Project ด้วย Depth Map + Camera Intrinsics → ตำแหน่ง 3D ใน Camera Frame

**B5 — Scale Verification:** เปรียบเทียบระยะห่างระหว่าง Marker จาก iPhone กับจาก Intraoral Scan → ต้องตรงกัน ± 0.1 มม.

**B6 — 6DOF Computation:** SVD-based Rigid Body Estimation → Transformation Matrix (4×4) ต่อ Frame

### ส่วน C — Integration

**C1 — Registration:** ใช้ตำแหน่ง Marker จาก Intraoral Scan เป็น Anchor Points → Align Camera Frame → Dental Coordinate Frame + Zero Jaw Position (Team 1)

**C2 — CI-TRANSFORM Export:** JSON/XML ครบ Timestamp + Scale + Jaw Pose Matrix + Encrypted Patient ID ตาม PDPA

---

## 6. แผนการดำเนินงาน (Sprint Plan)

| Sprint | สัปดาห์ | กิจกรรมหลัก | สิ่งที่ต้องส่งมอบ |
|---|---|---|---|
| S0 | W1 1–7 มิ.ย. | ตั้ง Env, ศึกษา DiffSoup, Architecture Report | Architecture Doc + Env Setup |
| S1 | W2–3 8–21 มิ.ย. | Curvature Analysis Module (κ₁,κ₂ + QEM + Density Map) บน mesh ใบหน้า | โมดูลความโค้ง + Density Map (จมูก/ปาก/หูร้อน) |
| S2 | W4–5 22 มิ.ย.–5 ก.ค. | CG-Soup Initialization + ต่อ DiffSoup Pipeline | โมเดลหน้า CG-Soup < 5,000 สามเหลี่ยม |
| S3 | W6 6–12 ก.ค. | Regularization Loss + ปรับจูน + วัด PSNR/SSIM/LPIPS | รายงานผลโมเดล 3D |
| S4 | W7–8 13–26 ก.ค. | Marker Detection + 3D Localization + Scale Verification | สคริปต์ตรวจจับ Marker + ผล Scale |
| S5 | W9–10 27 ก.ค.–9 ส.ค. | 6DOF Rigid Body + Registration เข้า Dental Frame | โค้ด Transformation Matrix |
| S6 | W11 10–16 ส.ค. | CI-TRANSFORM Exporter + API Team 1 / Exocad + PDPA | ส่งออก CI-TRANSFORM สำเร็จ |
| S7 | W12–13 17–30 ส.ค. | ทดสอบอาสาสมัคร ≥ 10 คน: RMSE + fps | รายงานความแม่นยำ |
| S8 | W14 31 ส.ค.–6 ก.ย. | Performance Tuning + Final Documentation + Demo | ส่งมอบครบ |

---

## 7. ตัวชี้วัดประเมินผลสัมฤทธิ์ (KPIs)

**Track A — CG-Soup:**
- คุณภาพภาพ: PSNR, SSIM, LPIPS เทียบกับ DiffSoup Baseline
- จำนวน Triangle: < 5,000 ชิ้น
- Convergence Time: ลดลงเทียบกับ Random Initialization

**Track B — JawTrack:**
- RMSE ≤ 0.5 มม. เทียบกับระบบอ้างอิง
- fps ≥ 30 บน iPhone
- Scale Accuracy: ระยะห่าง Marker ± 0.1 มม. จาก Intraoral Scan

**Track C — Integration:**
- CI-TRANSFORM Import สำเร็จเข้า Exocad / Team 1 API
- Data Integrity: ทุก record มี Timestamp + Scale ครบ

---

## 8. เงื่อนไขและข้อกำหนดทางเทคนิค (Constraints)

- **Hardware:** iPhone XR+ (TrueDepth), SHINING 3D Intraoral Scanner, Fiducial Dot Markers, Mac + Xcode
- **Marker Protocol:** ต้องติดก่อนสแกน Intraoral ทุกครั้ง — ห้ามถอดก่อนยืนยันว่าสแกนสำเร็จ
- **Framework:** ARKit/AVFoundation (Swift) สำหรับ TrueDepth; PyTorch + DiffSoup (Python) สำหรับ CG-Soup
- **Coordinate System:** 6DOF ต้องอ้างอิง Dental Coordinate Frame จาก Intraoral Scan เสมอ
- **PDPA:** Patient ID เข้ารหัสก่อนส่ง API ลบข้อมูลดิบหลังประมวลผล

---

## 9. สิ่งที่ต้องส่งมอบ (Final Deliverables)

- Source Code — Git Repository พร้อม Pull Request ตามกฎ
- Technical Report — CG-Soup Quality + JawTrack Accuracy (Manual vs Marker-Based)
- Integration Report — การเชื่อมต่อ Team 1 API + CI-TRANSFORM Export
- Validation Data — อาสาสมัคร ≥ 10 คน
- คู่มือการใช้งาน + Demo Video

---

## 10. ความเสี่ยงและแนวทางรับมือ (Risks)

| ความเสี่ยง | แนวทางรับมือ |
|---|---|
| Intraoral Scan ไม่มี Marker (ข้อมูลวันแรก) | ต้องสแกนใหม่ WITH Markers ก่อนเริ่ม S4 |
| Marker หลุด/เลื่อน | ตรวจสอบก่อน/หลัง Session; สแกนใหม่ถ้าเลื่อน |
| iPhone ตรวจจับ Marker ไม่ได้ | กำหนดโปรโตคอลแสง; Fallback = ArUco Markers |
| ผิวหน้า non-rigid | Protocol ถ่าย neutral เข้มงวด |
| เชื่อมหน้า ↔ ฟัน ไม่มี overlap | ใช้ชุด "ยิ้มเห็นฟัน" หรือ bite jig เป็นสะพาน |
| API contract กับ Team 1 ล่าช้า | เริ่มคุยตอนนี้; Block S5 ถ้า Spec ยังไม่นิ่ง |
| DiffSoup โค้ดใหม่ 2026 | เผื่อ debug time S0–S2 |
| PDPA | ออกแบบ encryption + data deletion ตั้งแต่ S6 |

---

## 11. รายการอ้างอิง (References)

1. Tojo, K., Bickel, B., & Umetani, N. (2026). *DiffSoup: Direct Differentiable Rasterization of Triangle Soup.* CVPR 2026. https://arxiv.org/abs/2603.27151
2. Tojo, K. (2026). *DiffSoup Official Code.* https://github.com/kenji-tojo/diffsoup
3. Ungvichian, V., & Kanongchaiyos, P. (2011). *Mesh Simplification Using Principal Curvatures.* CMES, 77(3&4).
4. Garland, M., & Heckbert, P. S. (1997). *Surface Simplification Using Quadric Error Metrics.* SIGGRAPH '97.
5. Apple Inc. — ARKit, AVFoundation, Vision Framework Documentation.
6. exocad GmbH — exocad DentalCAD Documentation.

> **⚠️ หมายเหตุ:** Markers ต้องติดก่อนสแกน Intraoral เสมอ — นี่คือจุดเชื่อมโยงสำคัญที่สุดของทั้งโครงการ
