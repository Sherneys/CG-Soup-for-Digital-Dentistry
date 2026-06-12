# รายงานการทำงาน — 13 มิ.ย. 2569 (กลางดึก): S3 เต็มรูปแบบ + Head-Only Pipeline

> ต่อเนื่องจากรายงาน 12 มิ.ย. — โครงการ CG-Soup (ทั้งหน้า) + JawTrack

## สรุปย่อ

ปิดชุดการทดลอง S3: (1) เพิ่ม **LPIPS** ครบ KPI (2) สร้าง **head-only pipeline** (mask + crop) ตามโจทย์จริงของโครงการ — ผลกระโดด **+7 dB** (3) รัน **multi-seed 3 seeds** ได้ mean±SD (4) **ablation regularizer** ของเราเอง ข้อค้นพบสำคัญ: การโฟกัสที่วัตถุ (head-only) ให้ผลมากกว่าการเลือกวิธี init มาก และ buddha เป็น worst-case ของ curvature-guided เพราะผิวมีรายละเอียดสม่ำเสมอทั้งหัว

---

> 📊 **กราฟสรุปผลทั้งหมด:** `output/figures/s3_results.png` (สร้างซ้ำได้ด้วย `python src/plot_s3_results.py`)

## 1. เครื่องมือใหม่

| ไฟล์ | ทำอะไร |
|---|---|
| `src/eval_soup.py` | วัด PSNR/SSIM/**LPIPS (VGG)** จาก checkpoint โดยไม่ต้อง train ใหม่ + รองรับ masked metrics |
| `src/make_masks.py` | สร้าง mask วัตถุ 67 วิวอัตโนมัติ: crop coarse mesh ด้วยทรงกลม → เรนเดอร์ silhouette ผ่านกล้องทุกตัวด้วย diffsoup rasterizer |
| `diffsoup_train.py` (อัปเกรด) | `--seed` / `--reg_normal` (normal-consistency k-NN regularizer) / `--masks` (masked L1+SSIM+opacity loss) / `--crop_center,--crop_radius` |
| `curvature_init.py` (อัปเกรด) | `--crop-center/--crop-radius` — สร้าง seeds เฉพาะหัว |

ค่า crop หัว buddha ที่ลงตัว (ไล่ตรวจ overlay 6 รอบ): center `[0.90, 0.22, 1.25]` radius `1.45`

## 2. ผลหลัก: Head-only @5,000 faces, 3 seeds (mean±SD)

| Init | PSNR (dB) ↑ | SSIM ↑ | LPIPS ↓ |
|---|---|---|---|
| **Curvature** | **22.375 ± 0.017** | **0.8020 ± 0.0030** | **0.2030 ± 0.0037** |
| Random | 22.307 ± 0.081 | 0.7993 ± 0.0044 | 0.2039 ± 0.0023 |

**เทียบกับ full-scene @5,000 faces (12 มิ.ย.): PSNR 15.38 → 22.38 (+7.0 dB), SSIM 0.526 → 0.802**

ข้อสรุปแบบตรงไปตรงมา:

1. **Head-only pipeline คือตัวเปลี่ยนเกม** — งบสามเหลี่ยมทั้งหมดถูกเทให้วัตถุ + วัดเฉพาะส่วนที่แคร์ → คุณภาพเข้าโซนใช้งานจริง (SSIM 0.80)
2. **ในสนาม head-only, curvature ≈ random ภายใน noise** (+0.07 dB ภายใน ~1SD ของ random) — ต่างจาก full-scene ที่ curvature ชนะชัด (+0.44–0.51 dB) เหตุผล: พอ crop เหลือแค่หัว จุด SfM ของ random ก็เกาะวัตถุหมดแล้ว ความได้เปรียบเชิงตำแหน่งหาย
3. **Curvature นิ่งกว่าอย่างเห็นได้ชัด**: PSNR SD 0.017 vs 0.081 (แคบกว่า ~5 เท่า) — ทำซ้ำได้เสถียร เป็นคุณสมบัติที่มีค่าต่อ pipeline คลินิก
4. ⚠️ **buddha คือ worst-case ของวิธีเรา**: ผิวเป็นเม็ดผมโค้งถี่ทั่วทั้งหัว → density map แทบ uniform → ไม่มีที่ให้ "ฉลาดกว่า random" ส่วน**หน้าคนจริง**มีแก้ม/หน้าผากแบนกว้าง vs ตา/ปาก/จมูกโค้ง = สนามที่ curvature-guided ออกแบบมาเพื่อมัน — คาดว่า margin จะกลับมากว้างเมื่อใช้ข้อมูลชุด A

## 3. Ablation: Normal-consistency regularizer (curvature @5k, seed 0)

| λ | PSNR | SSIM | LPIPS |
|---|---|---|---|
| 0 (baseline) | **22.355** | **0.8048** | 0.2033 |
| 0.01 | 22.066 | 0.7976 | 0.2037 |
| 0.1 | 21.527 | 0.7637 | 0.2342 |

**Regularizer ไม่ช่วย image metrics** (ยิ่งแรงยิ่งแย่) — สมเหตุสมผล: บังคับให้ normal เรียงกัน = ลดอิสระในการ fit ภาพ คุณค่าที่อาจมีคือ**คุณภาพพื้นผิวเชิงเรขาคณิต** (เรียบ ไม่มีหนาม) ซึ่งสำคัญตอน S5 registration กับ intraoral scan — ต้องวัดด้วย geometric metric (เช่น chamfer distance ไป coarse mesh) ไม่ใช่ photometric → ตั้งเป็นงานต่อ ค่า default แนะนำ **λ=0 สำหรับ KPI รายภาพ**

## 4. LPIPS full-scene ย้อนหลัง (เติม KPI ตาราง 12 มิ.ย. ให้ครบ)

| Budget | Curv LPIPS ↓ | Rand LPIPS ↓ |
|---|---|---|
| 15,000 | **0.5749** | 0.5930 |
| 10,000 | 0.6060 | **0.5997** |
| 5,000 | **0.6075** | 0.6127 |

(curvature ชนะ 2/3 — จุดที่แพ้คือ 10k)

## งานถัดไป

1. **ทดลองที่ budget ต่ำกว่า** (2,500 / 1,000 faces, head-only) — สมมติฐาน: margin ของ curvature กลับมาเมื่องบตึงจริง ๆ
2. **Geometric eval** สำหรับตัดสิน regularizer (chamfer → mesh_coarse)
3. **ข้อมูลหน้าคนจริง (ชุด A)** — สนามที่วิธีเราได้เปรียบโดยธรรมชาติ + mask เปลี่ยนเป็น face segmentation
4. (option showcase) `--downscale 2` หรือเช่า cloud GPU ≥24GB สำหรับ full res

## ไฟล์ที่เพิ่ม/แก้

| ไฟล์ | สถานะ |
|---|---|
| `src/eval_soup.py` | ใหม่ |
| `src/make_masks.py` | ใหม่ |
| `src/diffsoup_train.py` | แก้ — seed/reg/masks/crop |
| `src/curvature_init.py` | แก้ — crop |
| `output/buddha_sfm/dense/masks_4/` | ใหม่ — mask 67 วิว + overlay ตรวจสอบ |
| `output/head_curv_init.npz` | ใหม่ — seeds เฉพาะหัว |
| `output/diffsoup_head_*/` | ใหม่ — ผล 8 runs (3 seeds × 2 init + reg ×2) |
