# แจ้งขอบเขตโครงการที่ปรับปรุง — Team 4 (CP-2026-A4)

**ถึง:** รศ.ดร.พิษณุ คนองชัยยศ (ที่ปรึกษา) + Team 1
**จาก:** Team 4 (CP-2026-A4)
**วันที่:** 11 มิถุนายน 2569
**เรื่อง:** ยืนยันขอบเขตโครงการ CG-Soup + JawTrack และแจ้งการตัดสินใจสำคัญด้านเทคนิค

---

## 1. ขอบเขตที่ยืนยันแล้ว (Confirmed Scope)

หลังจากศึกษาวิธีการทางเทคนิค เยี่ยมชมคลินิก และทดสอบเบื้องต้น Team 4 ขอยืนยันขอบเขตโครงการดังนี้:

### Track A — CG-Soup (ใบหน้า Extra-Oral)
- **สิ่งที่ทำ:** สร้างแบบจำลองสามมิติของ **ใบหน้าทั้งหน้า (extra-oral)** จากภาพถ่ายหลายมุมขณะยิ้มเห็นฟัน โดยใช้วิธี Curvature-Guided Neural Triangle Soup ต่อยอดจาก DiffSoup (CVPR 2026)
- **ขอบเขตชัดเจน:** ภายนอกช่องปาก (extra-oral) — จมูก ริมฝีปาก ใบหน้าทั้งหน้า
- **ผลลัพธ์:** แบบจำลอง < 5,000 สามเหลี่ยม

### Track B — JawTrack (Marker-Based)
- **สิ่งที่ทำ:** วัดการเคลื่อนไหวขากรรไกร 6DOF ด้วย **Fiducial Dot Markers** ที่ติดบนฟัน
- **วิธีการ:** Intraoral Scan WITH Markers (SHINING 3D) + iPhone TrueDepth + SVD-based Rigid Body Estimation
- **การตัดสินใจสำคัญ:** ใช้ Physical Markers ไม่ใช่ Software Landmarks หรือ FreeMoCap Skeleton

### Track C — Integration
- Register ข้อมูลทั้งสอง Track → ส่งออก CI-TRANSFORM (JSON/XML) → Exocad / Team 1 API

---

## 2. การตัดสินใจทางเทคนิค: ทำไมถึงใช้ Physical Fiducial Markers

เหตุผลที่เลือกใช้ Physical Markers แทน FreeMoCap หรือ Software Landmarks:

| ปัจจัย | Physical Markers | FreeMoCap / Software Landmarks |
|---|---|---|
| **Scale Accuracy** | ไม่มีปัญหา — Intraoral Scanner มี Absolute Scale | ต้องแก้ Scale Ambiguity (ซับซ้อน) |
| **Coordinate Bridge** | Markers อยู่ใน Intraoral Scan = ใน Dental Frame ทันที | ต้องหาวิธี register ฟันกับใบหน้า |
| **Clinical Setting** | ใช้ได้จริงในคลินิก ไม่ต้องติด Sensor บนผิวหนัง | ยาก ถ้าผู้ป่วยขยับ |
| **RMSE Target** | ≤ 0.5 mm ทำได้ | ไม่แน่ใจ |
| **Hardware** | iPhone TrueDepth + SHINING 3D (มีอยู่แล้ว) | ต้องการ Camera Setup เพิ่ม |

---

## 3. สิ่งที่จำเป็นต้องทราบจากการเยี่ยมคลินิก

วันที่ 11 มิถุนายน 2569 — เยี่ยมคลินิกพร้อมอุปกรณ์ SHINING 3D Scanner ครบ

**ได้รับ:**
- Intraoral Scan (STL/OBJ) ✅
- วิดีโอขากรรไกร (iPhone) ✅

**ต้องตรวจสอบ:**
- ❓ Intraoral Scan มี Fiducial Dot Markers ติดอยู่หรือไม่?
  - ถ้ามี → เดินหน้า Track B ได้เลย
  - ถ้าไม่มี → ต้องนัดสแกนใหม่โดยติด Markers ก่อน (prerequisite ของ Sprint S4)

---

## 4. คำถามสำหรับ Team 1 (API Contract — ต้องการก่อน Sprint S5)

เพื่อออกแบบ CI-TRANSFORM Export และ Registration ให้ถูกต้อง Team 4 ต้องการ Spec ดังนี้:

**คำถามที่ 1:** Zero Jaw Position คืออะไร และนิยามไว้ที่จุดไหนในกรอบพิกัดของ Team 1?

**คำถามที่ 2:** CI-TRANSFORM ที่ Team 1 รับได้คือ JSON หรือ XML หรือทั้งสอง? มี Schema หรือ Example ให้ได้เลยไหม?

**คำถามที่ 3:** Coordinate Frame ของ Team 1 อ้างอิงจากอะไร (Intraoral Scan origin / หน้าผู้ป่วย / อื่น)?

**คำถามที่ 4:** ต้องส่ง CI-TRANSFORM แบบ Real-time Streaming หรือ Post-processing batch?

**คำถามที่ 5:** มี Encryption / Authentication Requirement สำหรับ Patient ID ในระบบ Team 1 ไหม?

**คำถามที่ 6:** Endpoint / API Version ที่ Team 1 จะ expose ให้ Team 4 test คืออะไร และพร้อมใช้เมื่อไหร่?

> **⚠️ สำคัญ:** Team 4 ต้องการ API Spec จาก Team 1 **ก่อนเริ่ม Sprint S5** (ประมาณ 27 กรกฎาคม 2569) มิฉะนั้น Track C อาจต้องเลื่อน

---

## 5. ขั้นตอนถัดไป (Next Steps)

| Action | ผู้รับผิดชอบ | Deadline |
|---|---|---|
| ตรวจสอบ Intraoral Scan วันนี้ว่ามี Markers ไหม | Team 4 | ASAP |
| ถ่ายภาพใบหน้าหลายมุม ≥ 40 ใบ (extra-oral) | Team 4 | ก่อน Sprint S2 |
| ตอบ API Contract Questions ข้อ 1–6 | Team 1 | ก่อน 27 ก.ค. 2569 |
| Confirm Zero Jaw Position definition | Team 1 + Advisor | ก่อน Sprint S5 |
| Review scope confirmation นี้ | รศ.ดร.พิษณุ | ตามสะดวก |

---

*หมายเหตุ: เอกสารนี้เป็น Draft — Team 4 ต้องส่งให้ที่ปรึกษาและ Team 1 ด้วยตนเอง*
