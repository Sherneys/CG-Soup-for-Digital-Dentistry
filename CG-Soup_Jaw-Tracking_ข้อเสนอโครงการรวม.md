# ข้อเสนอโครงการวิจัย (Research Project Proposal)

## ระบบสร้างแบบจำลองใบหน้าสามมิติเชิงพลวัตด้วยการเริ่มต้นโครงข่ายรูปสามเหลี่ยมอิสระแบบนำทางด้วยความโค้ง สำหรับการติดตามการเคลื่อนไหวขากรรไกรในงานทันตกรรมดิจิทัล
### Curvature-Guided Neural Triangle Soup Modeling for Dynamic Facial Representation and Jaw Motion Tracking (CG-Soup for Digital Dentistry)

**รหัสโครงการ:** CP-2026-A3 | **ทีม:** Team 3 | **ที่ปรึกษา:** รศ.ดร.พิษณุ คนองชัยยศ
**ระยะเวลา:** 14 สัปดาห์ (280 ชั่วโมง) เริ่ม 1 มิถุนายน 2569

---

## บทคัดย่อ (Abstract)

งานทันตกรรมดิจิทัล (Digital Dentistry) เช่น การออกแบบครอบฟัน/ฟันปลอมผ่านระบบ Exocad และการวิเคราะห์การสบฟัน จำเป็นต้องอาศัยองค์ประกอบสองส่วนพร้อมกัน คือ (1) แบบจำลองใบหน้าสามมิติ (extra-oral) ที่มีความถูกต้องเชิงเรขาคณิตสูงและมีน้ำหนักเบาพอจะประมวลผลแบบเรียลไทม์ เพื่อใช้เป็นพื้นผิวอ้างอิงของการเคลื่อนไหวขากรรไกรและเป็นตัวเชื่อมกับแบบจำลองฟันจาก Intraoral Scan และ (2) ข้อมูลการเคลื่อนไหวของขากรรไกรที่แม่นยำ โครงการนี้เสนอ **CG-Soup** ซึ่งเป็นวิธีการแกนหลัก (core method) ที่ต่อยอดจากสถาปัตยกรรม DiffSoup โดยใช้การวิเคราะห์ความโค้งหลัก (Principal Curvatures) นำทางการเริ่มต้นโครงข่ายรูปสามเหลี่ยมอิสระ เพื่อสร้างแบบจำลองใบหน้าสามมิติที่เก็บรายละเอียดบริเวณความโค้งสูง (เช่น จมูก ริมฝีปาก หู ขอบตา และคาง) ได้คมชัด ขณะที่ใช้จำนวนรูปสามเหลี่ยมน้อยกว่า 5,000 ชิ้น ส่วนข้อมูลฟันและเหงือกใช้จาก Intraoral Scan (IOS) ของคลินิกเท่านั้น จากนั้นจึงนำข้อมูลการเคลื่อนไหวขากรรไกรแบบ 6DOF ที่จับด้วย iPhone TrueDepth ร่วมกับ FreeMoCap มาทำ Registration ซ้อนทับบนแบบจำลอง CG-Soup และส่งออกในมาตรฐาน CI-TRANSFORM เข้าสู่ระบบ Exocad คุณลักษณะของใบหน้าที่ความโค้งสูงกระจุกตัวเฉพาะบางบริเวณ (จมูก ปาก หู) ขณะที่แก้มและหน้าผากค่อนข้างราบ เป็นจุดเด่นที่ทำให้การเริ่มต้นแบบนำทางด้วยความโค้งเหมาะสมกับโจทย์นี้เป็นพิเศษ

---

## 1. ความเป็นมาและความสำคัญของปัญหา (Problem Statement)

การสร้างแบบจำลองและติดตามการเคลื่อนไหวขากรรไกรเพื่อใช้ในงานทันตกรรมดิจิทัล ต้องเผชิญกับความท้าทายสองด้านที่เกี่ยวเนื่องกัน:

**ด้านโจทย์ (Application): การติดตามการเคลื่อนไหวขากรรไกร (Jaw Tracking)** — การวิเคราะห์การสบฟันและการออกแบบชิ้นงานทันตกรรมที่แม่นยำต้องอาศัยข้อมูลการเคลื่อนไหวของขากรรไกร (Jaw Kinematics) ที่สัมพันธ์กับโมเดลฟันของผู้ป่วย แต่ระบบดั้งเดิมพึ่งพา Articulator เชิงกลหรืออุปกรณ์ออปติคัลราคาสูง ทำให้เข้าถึงยากและมีต้นทุนสูง การใช้ iPhone TrueDepth ร่วมกับ FreeMoCap จึงเป็นทางเลือกที่เข้าถึงได้ แต่ยังต้องการแบบจำลองใบหน้าสามมิติที่ถูกต้องและเบาพอจะใช้เป็นพื้นผิวอ้างอิงให้การเคลื่อนไหวมาซ้อนทับได้แบบเรียลไทม์ และเชื่อมต่อกับแบบจำลองฟันจาก Intraoral Scan ได้

**ด้านวิธีการ (Method): การสร้างตัวแทนฉากสามมิติ** — เทคโนโลยี DiffSoup ใช้กลุ่มของรูปสามเหลี่ยมอิสระ (Unstructured Triangle Soup) จำนวนน้อยชิ้นร่วมกับความทึบแสงแบบสุ่ม (Stochastic Opacity Masking) ทำให้หาอนุพันธ์และเรนเดอร์ได้รวดเร็วบนอุปกรณ์ทั่วไป อย่างไรก็ตาม กระบวนการเริ่มต้น (Initialization) ของ DiffSoup ยังพึ่งพาการกระจายจุดศูนย์กลางรูปสามเหลี่ยมแบบสุ่มหรืออิงจาก Point Cloud แบบหยาบ โดยปราศจากความเข้าใจในบริบททางเรขาคณิตล่วงหน้า (Geometric Priors) ส่งผลให้ใช้เวลาปรับให้เหมาะสมยาวนาน เกิดความซ้ำซ้อนของรูปสามเหลี่ยมในบริเวณพื้นที่ราบ และสูญเสียรายละเอียดในบริเวณความโค้งสูง ซึ่งเป็นปัญหาวิกฤตสำหรับพื้นผิวใบหน้าที่มีบริเวณความโค้งสูงอย่างจมูก ริมฝีปาก หู และขอบตา ปะปนกับบริเวณราบขนาดใหญ่อย่างแก้มและหน้าผาก

**กรอบการบูรณาการของโครงการ:** โครงการนี้กำหนดให้ **การติดตามการเคลื่อนไหวขากรรไกรเป็นโจทย์หลัก** และใช้ **CG-Soup เป็นแกนวิธีการ (core methodology)** ที่ผลิตแบบจำลองใบหน้า (extra-oral) ซึ่งแม่นยำเพียงพอโดยเฉพาะบริเวณรอบปากและคาง (โซนที่ขากรรไกรเคลื่อนไหว) และเบาพอจะรองรับการเคลื่อนไหวแบบพลวัต โดยอาศัยข้อสังเกตว่าพื้นผิวใบหน้ามีลักษณะเหมาะสมกับการเริ่มต้นแบบนำทางด้วยความโค้งอย่างยิ่ง กล่าวคือ บริเวณจมูก/ริมฝีปาก/หู/ขอบตา/คางต้องการรายละเอียดถี่ ขณะที่บริเวณแก้มและหน้าผากค่อนข้างราบและต้องการรูปสามเหลี่ยมน้อยกว่า ทั้งนี้ข้อมูลฟันและเหงือกไม่ได้สร้างจาก CG-Soup แต่ใช้จาก Intraoral Scan ของคลินิก โดยแบบจำลองใบหน้าทำหน้าที่เป็นตัวเชื่อม (registration bridge) ระหว่างข้อมูลการเคลื่อนไหวกับ Intraoral Scan

---

## 2. วัตถุประสงค์ (Objectives)

1. พัฒนาวิธีการ CG-Soup ที่ใช้ความโค้งหลักนำทางการเริ่มต้นโครงข่ายรูปสามเหลี่ยมบน DiffSoup เพื่อสร้างแบบจำลองใบหน้าสามมิติ (extra-oral) คุณภาพสูงที่ใช้รูปสามเหลี่ยมต่ำกว่า 5,000 ชิ้น
2. พัฒนา Engine ติดตามการเคลื่อนไหวขากรรไกรแบบ 6DOF ด้วย iPhone TrueDepth และ FreeMoCap ให้มีความคลาดเคลื่อน RMSE ≤ 0.5 มม. และทำงานที่ ≥ 30 fps
3. บูรณาการสองส่วนเข้าด้วยกัน โดยทำ Registration ข้อมูลการเคลื่อนไหวซ้อนทับบนแบบจำลอง CG-Soup และส่งออกมาตรฐาน CI-TRANSFORM (JSON/XML) เข้าสู่ระบบ Exocad
4. ประเมินประสิทธิภาพของระบบเทียบกับ Baseline ทั้งด้านคุณภาพการสร้างโมเดลและความแม่นยำการติดตาม

---

## 3. ขอบเขตงาน (Scope of Work)

พัฒนาระบบที่ประกอบด้วยสองส่วนหลักซึ่งทำงานต่อเนื่องกัน ได้แก่ (ก) วิธีการ CG-Soup สำหรับสร้างแบบจำลองใบหน้าสามมิติ (extra-oral) จากภาพถ่ายใบหน้าหลายมุมมองโดยนำทางด้วยความโค้ง และ (ข) Engine ติดตามการเคลื่อนไหวขากรรไกร (Jaw Kinematics) ด้วย iPhone TrueDepth และ FreeMoCap (v1.6.1+) เพื่อนำข้อมูล 6DOF ไปทำ Registration กับแบบจำลองใบหน้า CG-Soup และ Intraoral Scan (กรอบพิกัดอ้างอิงของข้อมูลฟัน) และส่งออกเป็นมาตรฐาน CI-TRANSFORM เข้าสู่ระบบ Exocad ทั้งนี้การสร้างแบบจำลองฟัน/ช่องปากอยู่นอกขอบเขตของโครงการ โดยใช้ Intraoral Scan ของคลินิกแทน

---

## 4. ข้อกำหนดข้อมูลเข้าและผลลัพธ์ (Input and Output Specifications)

**ข้อมูลเข้า (Input):**

- **ชุดภาพถ่ายหลายมุมมอง (Multi-view RGB Images):** ภาพถ่ายใบหน้า (extra-oral) กวาดรอบหน้า ~180° ครอบคลุมหน้าผากถึงใต้คางรวมหูทั้งสองข้าง สีหน้า neutral นิ่งตลอดการถ่าย พร้อมพารามิเตอร์การโพสของกล้อง (Camera Poses) จากอัลกอริทึม Structure-from-Motion (SfM) และชุดภาพ "ยิ้มเห็นฟัน" เพิ่มเติมสำหรับใช้เชื่อมใบหน้ากับ Intraoral Scan ตอน Registration
- **โครงร่างตาข่ายขั้นต้น (Initial Coarse Mesh / Point Cloud):** ข้อมูลจุดยอดขั้นต้นของใบหน้าที่สกัดแบบหยาบจาก SfM (หรือ TrueDepth) เพื่อใช้เป็นโครงสร้างตั้งต้นในการวิเคราะห์เรขาคณิต
- **ข้อมูลการเคลื่อนไหวขากรรไกร:** สตรีมภาพเชิงลึกจาก iPhone TrueDepth สำหรับสกัดการเคลื่อนไหว 6DOF
- **โมเดลอ้างอิง Intraoral Scan:** แหล่งข้อมูลฟันและเหงือกของระบบ (บน + ล่าง + bite) และใช้เป็นกรอบพิกัด (Coordinate Frame) อ้างอิงสำหรับ Registration

**ผลลัพธ์ (Output):**

- **แบบจำลองใบหน้าสามมิติ (3D Facial Model):** ชุดข้อมูล Triangle Soup ที่ปรับให้เหมาะสมแล้ว มีจำนวนรูปสามเหลี่ยมต่ำกว่า 5,000 ชิ้น แต่ยังคงรูปทรงเรขาคณิตของใบหน้าถูกต้อง โดยเฉพาะบริเวณรอบปากและคางซึ่งเป็นโซนการเคลื่อนไหวของขากรรไกร
- **ภาพสังเคราะห์มุมมองใหม่ (Novel View Synthesis):** ภาพเรนเดอร์ความละเอียดสูง ขอบเขต (Silhouette) คมชัด รักษารายละเอียดความถี่สูง (High-frequency Details) ของใบหน้า เช่น จมูก ริมฝีปาก และหู
- **ข้อมูลการเคลื่อนไหวที่ผ่าน Registration:** ข้อมูล 6DOF ในมาตรฐาน CI-TRANSFORM (JSON/XML) พร้อม Timestamp และค่า Calibration Scale พร้อมนำเข้าระบบ Exocad

---

## 5. ระเบียบวิธีและกระบวนการบูรณาการ (Methodology & Integration)

กระบวนการแบ่งเป็นสามส่วนต่อเนื่องกัน โดยมี CG-Soup เป็นแกนวิธีการที่ผลิตแบบจำลอง และมี Jaw Tracking เป็นโจทย์ที่นำแบบจำลองไปใช้งานเชิงพลวัต

### ส่วน A — แกนวิธีการ CG-Soup (3 ระยะ)

**ระยะที่ 1: การวิเคราะห์ความโค้งและพารามิเตอร์ทางเรขาคณิต (Curvature Analysis Phase)**
รับ Input เป็นโครงร่างแบบหยาบของใบหน้า และประยุกต์อัลกอริทึมจากงานวิจัย *Mesh Simplification Method Using Principal Curvatures and Directions* โดยคำนวณค่าความโค้งหลัก (Principal Curvatures) ทิศทางความโค้ง และค่าความคลาดเคลื่อนแบบควอดริก (Quadric Error Metrics: QEM) ของแต่ละจุดยอด

**ระยะที่ 2: การสร้างตัวแทนสามเหลี่ยมแบบนำทาง (Curvature-Guided Initialization Phase)**
ใช้ข้อมูลจากระยะที่ 1 สร้างแผนที่ความหนาแน่น (Density Map) โดยบังคับให้ระบบสร้างรูปสามเหลี่ยมขนาดเล็กจำนวนมากในบริเวณที่มีความโค้งตั้งฉากสัมบูรณ์สูง (Absolute Normal Curvature) เช่น จมูก ริมฝีปาก หู ขอบตา และคาง เพื่อเก็บรายละเอียดมุมและขอบ ขณะเดียวกันลดจำนวนและขยายขนาดรูปสามเหลี่ยมในบริเวณพื้นที่ราบ (เช่น แก้มและหน้าผาก) ที่มีค่าความเบี่ยงเบนของมุมต่ำ

**ระยะที่ 3: การหาอนุพันธ์และกำหนดสมการการสูญเสีย (Differentiable Optimization Phase)**
นำโครงสร้างรูปสามเหลี่ยมที่จัดระเบียบแล้วเข้าสู่ท่อส่งข้อมูลการเรนเดอร์ของ DiffSoup และเพิ่มสมการการลงโทษเชิงแผนผัง (Regularization Loss) จากค่าความเบี่ยงเบนของมุมและระนาบคู่ (Angular and Dihedral Deviations) ทำงานร่วมกับสมการสูญเสียสี (Color Loss) และสมการอนุพันธ์ของขอบ (Edge-gradient) เพื่อบีบบังคับให้โครงข่ายอัปเดตค่าน้ำหนักของ Neural Textures และความทึบแสงแบบทวิภาค (Binary Opacity) โดยไม่ทำให้แผ่นรูปสามเหลี่ยมบิดเบี้ยวผิดจากความโค้งทางกายภาพ

### ส่วน B — การติดตามการเคลื่อนไหวขากรรไกรและการ Registration

**การจับการเคลื่อนไหว 6DOF:** พัฒนาโมดูลสกัดการเคลื่อนไหวจาก iPhone TrueDepth ร่วมกับ FreeMoCap (v1.6.1+) พร้อมการทำ Calibration สเกลทุกครั้งก่อนเริ่มงาน เพื่อจัดการปัญหา "Scale Ambiguity" ของ FreeMoCap

**การ Registration:** คำนวณ Transformation Matrix เพื่อนำการเคลื่อนไหว (Jaw Jig) มาซ้อนทับกับแบบจำลองใบหน้า CG-Soup และ Intraoral Scan ในกรอบพิกัดเดียวกัน โดยใช้จุด Landmark ที่ Team 1 กำหนดเป็นจุดอ้างอิง (Zero Jaw Position) ทั้งนี้เนื่องจากใบหน้า (extra-oral) กับ Intraoral Scan แทบไม่มีพื้นผิวซ้อนทับกัน จึงใช้ชุดภาพ "ยิ้มเห็นฟัน" หรือ bite jig เป็นสะพานเชื่อมสองกรอบพิกัด (รายละเอียดตกลงร่วมกับ Team 1)

### ส่วน C — การบูรณาการและการส่งออก

ส่งข้อมูลการเคลื่อนไหวในมาตรฐาน CI-TRANSFORM (JSON/XML) เข้าสู่ API ของ Team 1 และระบบ Exocad โดยข้อมูลทุกชุดต้องมี Timestamp และค่า Calibration Scale ที่ถูกต้องก่อนบันทึก และต้องปฏิบัติตามวงจรชีวิตข้อมูล (CI Lifecycle) ตามข้อกำหนด PDPA

---

## 6. แผนการดำเนินงานรายสัปดาห์ (Detailed Sprint Plan)

โครงการเริ่ม 1 มิถุนายน 2569 รวม 14 สัปดาห์ (280 ชั่วโมง) แบ่งเป็น 3 เฟส: เฟส 1 สร้างแบบจำลอง CG-Soup, เฟส 2 ติดตามขากรรไกรและ Registration, เฟส 3 บูรณาการและประเมินผล

| Sprint | สัปดาห์ | ช่วงเวลา | กิจกรรมหลัก (Key Activities) | สิ่งที่ต้องส่งมอบ (Deliverables) |
|---|---|---|---|---|
| S0 | W1 | 1–7 มิ.ย. | ตั้งสภาพแวดล้อม, ศึกษา DiffSoup + FreeMoCap v1.6.1+, เตรียมชุดข้อมูลภาพหลายมุม/SfM | รายงาน Architecture และเครื่องมือที่ใช้ |
| S1 | W2–3 | 8–21 มิ.ย. | พัฒนา Curvature Analysis (Principal Curvatures, QEM) จากโครงร่างหยาบ | โมดูลวิเคราะห์ความโค้ง + Density Map |
| S2 | W4–5 | 22 มิ.ย.–5 ก.ค. | Curvature-Guided Initialization + ต่อท่อ Differentiable Optimization ของ DiffSoup | แบบจำลอง CG-Soup เบื้องต้น (<5,000 ชิ้น) |
| S3 | W6 | 6–12 ก.ค. | เพิ่ม Regularization Loss (Angular/Dihedral) + ปรับจูน, วัด PSNR/SSIM/LPIPS เทียบ Baseline | รายงานผลการสร้างแบบจำลอง 3D |
| S4 | W7–8 | 13–26 ก.ค. | พัฒนา Jaw Tracking 6DOF (iPhone TrueDepth) + Calibration สเกล (จัดการ Scale Ambiguity) | สคริปต์สกัด Motion Data + ผลการ Calibrate |
| S5 | W9–10 | 27 ก.ค.–9 ส.ค. | Registration: นำ Motion 6DOF มาซ้อนทับแบบจำลอง CG-Soup, กำหนด Zero Jaw Position ร่วมกับ Team 1 | Code การคำนวณ Transformation Matrix |
| S6 | W11 | 10–16 ส.ค. | ระบบส่งออก CI-TRANSFORM (JSON/XML) เข้า API Team 1 / Exocad | การเชื่อมต่อ API และบันทึก CI-TRANSFORM |
| S7 | W12–13 | 17–30 ส.ค. | ทดสอบกับอาสาสมัคร ≥10 คน, วัด RMSE & fps, เปรียบเทียบ Manual vs FreeMoCap | รายงานการเปรียบเทียบความแม่นยำ |
| S8 | W14 | 31 ส.ค.–6 ก.ย. | ปรับจูน Performance, จัดทำ Final Documentation และ Demo Video | คู่มือการใช้งาน + Demo Video + รายงานฉบับสมบูรณ์ |

---

## 7. ตัวชี้วัดประเมินผลสัมฤทธิ์ (KPIs & Evaluation Metrics)

**ด้านการสร้างแบบจำลอง (CG-Soup):**

- คุณภาพภาพเรนเดอร์: PSNR, SSIM และ LPIPS บนชุดข้อมูลมาตรฐาน เทียบกับ DiffSoup แบบมาตรฐาน (Baseline)
- จำนวนรูปสามเหลี่ยมที่ใช้ (Primitive Count): ต่ำกว่า 5,000 ชิ้น
- ระยะเวลาลู่เข้า (Convergence Time): ลดลงเมื่อเทียบกับการเริ่มต้นแบบสุ่ม
- ความถูกต้องเชิงเรขาคณิต: ให้น้ำหนักบริเวณรอบปากและคาง (โซนการเคลื่อนไหวของขากรรไกร) เป็นหลัก เทียบกับข้อมูลอ้างอิง เช่น TrueDepth depth หรือ CBCT (กรณีได้รับอนุญาต)

**ด้านการติดตามขากรรไกร (Jaw Tracking):**

- ความแม่นยำ (Accuracy): RMSE ≤ 0.5 มม. เทียบกับระบบอ้างอิง
- สมรรถนะระบบ (Performance): ทำงานที่ ≥ 30 fps บน iPhone

**ด้านการบูรณาการและความถูกต้องของข้อมูล:**

- Integration: ข้อมูล Motion อยู่ในรูปแบบ JSON/XML พร้อมนำเข้าระบบ Exocad ตาม SRS
- Data Integrity: ข้อมูลทุกชุดมี Timestamp และค่า Calibration Scale ที่ถูกต้องก่อนบันทึก (CI-TRANSFORM)

---

## 8. เงื่อนไขและข้อกำหนดทางเทคนิค (Constraints & Shared Requirements)

- **Hardware:** ต้องใช้ iPhone XR ขึ้นไปที่มี TrueDepth Camera เท่านั้น และชุดอุปกรณ์ถ่ายภาพหลายมุมมองสำหรับ CG-Soup
- **Framework:** บังคับใช้เฉพาะ Apple Frameworks (ARKit, RealityKit, Vision, Accelerate) ร่วมกับ FreeMoCap (v1.6.1+) สำหรับส่วน Tracking และใช้ท่อส่งข้อมูล DiffSoup (PyTorch) สำหรับส่วน CG-Soup เพื่อลดการพึ่งพาบุคคลที่สาม
- **Standardization:** การเก็บค่า 6DOF ต้องอ้างอิง Coordinate Frame เดียวกับแบบจำลอง CG-Soup / Intraoral Scan เสมอ ผ่านการคำนวณจาก Landmark ที่ Team 1 กำหนด
- **PDPA:** ข้อมูลภาพใบหน้าและ Motion Track เป็นข้อมูลที่ระบุตัวตนผู้ป่วยได้โดยตรง ต้องได้รับความยินยอม (Consent) ก่อนถ่ายทุกครั้ง เข้ารหัสก่อนส่งผ่าน API และลบข้อมูลดิบหลังประมวลผลเสร็จตามสถานะ CI Lifecycle

---

## 9. สิ่งที่ต้องส่งมอบ (Final Deliverables)

- **Source Code:** งานพัฒนาทั้งหมดบน Git Repository (มีการทำ Pull Request ตามกฎ)
- **Technical Report:** รายงานวิจัยการสร้างแบบจำลอง CG-Soup และ Jaw Kinematics (Comparison Manual vs. FreeMoCap)
- **Integration Report:** รายงานการเชื่อมต่อกับระบบหลัก (Team 1) และการส่งออก XML/JSON
- **Validation Data:** ข้อมูลทดสอบจากอาสาสมัครอย่างน้อย 10 คน เพื่อยืนยันความแม่นยำ
- **คู่มือการใช้งานและ Demo Video**

> **คำแนะนำสำหรับทีมที่ 3:** เน้นการจัดการ "Scale Ambiguity" ของ FreeMoCap โดยเฉพาะการทำ Calibration สเกลทุกครั้งก่อนเริ่มงาน และประสานงานใกล้ชิดกับ Team 1 เพื่อกำหนด API Contract ในการดึงพิกัด Landmark ที่ใช้เป็นจุดอ้างอิง (Zero Jaw Position) เพื่อให้ข้อมูลจาก iPhone นำมาซ้อนทับ (Register) บนแบบจำลอง 3D ของคนไข้ได้อย่างแม่นยำ

---

## 10. รายการอ้างอิง (References)

**เทคโนโลยี Differentiable Rendering และ DiffSoup**

1. Tojo, K., Bickel, B., & Umetani, N. (2026). *DiffSoup: Direct Differentiable Rasterization of Triangle Soup for Extreme Radiance Field Simplification.* Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2026). https://arxiv.org/abs/2603.27151
2. Tojo, K. (2026). *DiffSoup Official Source Code Repository.* GitHub. https://github.com/kenji-tojo/diffsoup

**การลดทอนรายละเอียดโพลิกอนและความโค้ง (Mesh Simplification & Curvatures)**

3. Ungvichian, V., & Kanongchaiyos, P. (2011). *Mesh Simplification Method Using Principal Curvatures and Directions.* Computer Modeling in Engineering & Sciences (CMES), 77(3&4), 201–220. https://www.techscience.com/CMES/v77n3&4/25719
4. Garland, M., & Heckbert, P. S. (1997). *Surface Simplification Using Quadric Error Metrics.* Proceedings of SIGGRAPH '97, 209–216.

**งานวิจัยอ้างอิงเชิงทิศทาง (รศ.ดร.พิษณุ คนองชัยยศ)**

5. Kanongchaiyos, P. (2003). *Topology-Oriented Free-Form Deformations with Object-Shaped Lattices.* Proceedings of 7th CAD/Graphics, Macao, China, 271–276.
6. Kanongchaiyos, P., & Shinagawa, Y. (2000). *Articulated Reeb Graphs for Interactive Skeleton Animation.* Proceedings of 1st Multimedia Modeling (MMM2000), 451–467.
7. Bunlutangtum, R., & Kanongchaiyos, P. (2011). *Enhanced View-dependent Adaptive Grid Refinement for Animating Fluids.* Proceedings of the 10th VRCAI, 415–418.
8. Saenghaengtham, N., & Kanongchaiyos, P. (2006). *Using LBG Quantization for Particle-based Collision Detection Algorithm.* Journal of Zhejiang University SCIENCE (JZUS), 7, 1225–1232.

**เทคโนโลยีและเครื่องมือที่เกี่ยวเนื่อง**

9. Svitov, D., & Dahaghin, M. (2026). *NBAvatar: Neural Billboards Avatars with Realistic Hand-Face Interaction.* arXiv:2603.12063. https://arxiv.org/abs/2603.12063
10. FreeMoCap Project (v1.6.1+) — Free Motion Capture. https://freemocap.org
11. Apple Inc. — ARKit, RealityKit, Vision, Accelerate Frameworks.
12. exocad GmbH — exocad DentalCAD.
