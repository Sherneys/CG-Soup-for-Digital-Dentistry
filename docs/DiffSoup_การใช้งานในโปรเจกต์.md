# DiffSoup — วิธีใช้และการเชื่อมเข้าโปรเจกต์ CG-Soup

> อ้างอิง: Tojo, K., Bickel, B., & Umetani, N. (2026). *DiffSoup: Direct Differentiable Rasterization of Triangle Soup for Extreme Radiance Field Simplification.* CVPR 2026
> Repo: https://github.com/kenji-tojo/diffsoup

## บทบาทของ DiffSoup ในโปรเจกต์นี้

DiffSoup คือ **"เครื่อง optimize" หลักของฝั่งสร้างโมเดลหน้า** — รับภาพหลายมุม + camera pose + triangle soup ตั้งต้น แล้วใช้ differentiable rasterization ปรับตำแหน่ง/สีของสามเหลี่ยมจนเรนเดอร์ตรงกับภาพถ่าย

**นวัตกรรมของเรา (CG-Soup) คือเปลี่ยนวิธี "ตั้งต้น"** จาก random/MobileNeRF mesh เป็น **curvature-guided initialization** จาก density map ของเราเอง

## ตำแหน่งใน Pipeline

```
ภาพหน้า 40–80 ภาพ
   │
   ▼
src/sfm_pipeline.py (COLMAP)          ← เสร็จแล้ว (S1) ✅
   │  ได้ 2 อย่าง:
   ├── camera poses + ภาพ undistorted  ──────────────┐
   └── coarse mesh (mesh_coarse.ply)                 │
          │                                          │
          ▼                                          │
src/curvature_density.py               ← เสร็จแล้ว (S1) ✅
   │  ได้ density map (ตรงไหนโค้งมาก = ต้องการสามเหลี่ยมหนาแน่น)
   ▼
[โมดูลใหม่ S2] curvature-guided init   ← งานถัดไป
   │  sample สามเหลี่ยมตั้งต้น <5,000 ชิ้นตาม density map
   │  (จมูก/ปาก/ตา ถี่, แก้ม/หน้าผาก ห่าง)
   ▼
DiffSoup optimization loop             ← ใช้โค้ดจาก repo
   │  ปรับ vertex + สี ด้วย photometric loss
   │  (S3 เพิ่ม regularization loss ของเราเอง)
   ▼
โมเดลหน้า <5,000 สามเหลี่ยม → พื้นผิวอ้างอิงให้ jaw tracking (S4–S6)
```

## จุดเชื่อมที่เป็นรูปธรรม

1. **Input ของ DiffSoup ตรงกับ output ของเราอยู่แล้ว** — `examples/01_mip360.py` โหลด scene จาก COLMAP format ซึ่งคือสิ่งที่ `sfm_pipeline.py` สร้างใน `output/<ชื่อ>/` (sparse model + ภาพ undistorted) → ชี้ `--scene_root` มาที่ workspace ของเราได้เกือบตรง ๆ
2. **จุดที่เราเข้าไปแก้คือขั้น initialization** — repo มี 2 ทางตั้งต้น: จาก mesh (MobileNeRF) หรือ random (`03_random_init.py`) ของเราเขียนตัวที่สาม: อ่าน density map จาก `curvature_density.py` แล้ววางสามเหลี่ยมตั้งต้นตามความหนาแน่น ก่อนส่งเข้า optimization loop เดิม
3. **Baseline สำหรับ S3 คือ repo เขาเอง** — รัน DiffSoup แบบ random init บนข้อมูลเดียวกัน วัด PSNR/SSIM/LPIPS เทียบกับ curvature-guided ของเรา ที่จำนวนสามเหลี่ยมเท่ากัน (KPI ในข้อเสนอโครงการ)

## วิธีติดตั้ง (สูตรที่ใช้ได้จริงบนเครื่องนี้ — ติดตั้งสำเร็จ 12 มิ.ย. 2569)

Repo ถูก clone ไว้ที่ **`D:\Project\diffsoup`** และติดตั้งเข้า `.venv` ของโปรเจกต์แล้ว

**Prerequisites ที่ลงไว้แล้ว:**
- VS 2022 Build Tools + C++ workload (MSVC 14.44) — ผ่าน `winget install Microsoft.VisualStudio.2022.BuildTools`
- CUDA Toolkit 12.8 ที่ `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8` — ผ่าน `winget install Nvidia.CUDA -v 12.8` (⚠️ nvcc **ไม่อยู่ใน PATH** ต้อง set เอง)
- ใน venv: `uv pip install cmake ninja scikit-build-core nanobind` + runtime deps (`open3d imageio lpips pytorch_msssim scikit-image tqdm`)

**คำสั่ง build/ติดตั้งใหม่ (กรณีอัปเดต repo):**

```powershell
Import-Module "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" -Arch amd64 -SkipAutomaticLocation
$env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
$env:PATH = "$env:CUDA_PATH\bin;$env:PATH"
$env:CMAKE_GENERATOR = "Ninja"
$env:CMAKE_ARGS = "-DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler -DCMAKE_CXX_FLAGS=-D__restrict__=__restrict"
uv pip install D:\Project\diffsoup --python D:\Project\CG-Soup-for-Digital-Dentistry\.venv\Scripts\python.exe
```

**Workaround 3 จุดที่จำเป็นบน Windows (ห้ามตัดออก):**
1. `CMAKE_GENERATOR=Ninja` — generator แบบ Visual Studio/MSBuild หา `CudaToolkitDir` ไม่เจอ
2. `-allow-unsupported-compiler` — MSVC 14.44 ใหม่กว่าที่ nvcc 12.8 รองรับอย่างเป็นทางการ
3. `-D__restrict__=__restrict` — โค้ด header ใช้ `__restrict__` (GCC syntax) ซึ่ง MSVC ไม่รู้จัก

**ตอนรัน examples:** ต้อง `$env:PYTHONUTF8 = "1"` ไม่งั้นตายตอน print ตัวอักษร "→" (console เป็น cp1252)

## คำสั่งหลักจาก repo

| คำสั่ง | ใช้ทำอะไร |
|---|---|
| `python examples\01_mip360.py --scene_root <COLMAP scene>` | Train จาก scene แบบ COLMAP — **ตรงกับ pipeline ของเรา** |
| `python examples\02_synthetic.py --scene lego` | Train scene สังเคราะห์ (Blender) — ไว้ทดสอบ env |
| `python examples\03_random_init.py --scene lego` | Train จาก random init — **baseline ของ S3** |
| `python examples\04_view_results.py --ckpt <final_params.pt>` | Viewer แบบ interactive (ไม่ต้องใช้ CUDA, ติดตั้ง `pip install -v viewer\` ก่อน) |
| `python examples\05_benchmark_fps.py --ckpt ... --scene_root ...` | วัด FPS |
| `python examples\06_export_web.py --ckpt ...` | Export เป็น web viewer (`cd web; python -m http.server 8080`) |

ผลลัพธ์ training ออกที่ `results/<example>/<scene>/` (checkpoint + metrics)

## สถานะ (12 มิ.ย. 2569)

1. ~~Clone + build DiffSoup เข้า `.venv`~~ ✅ เสร็จแล้ว
2. ~~รัน example ยืนยัน build~~ ✅ smoke test 200 steps บน buddha ผ่านครบทุกขั้น (training, resample, checkpoint, eval)
3. ~~ป้อน scene buddha เข้า `01_mip360.py`~~ ✅ จุดเชื่อมทำงานตรง ๆ — ใช้ `--scene_root output\buddha_sfm\dense --downscale 1` (loader อ่าน `dense/sparse` + `dense/images` ของ COLMAP 4.x ได้เลย)
4. ~~เขียนโมดูล S2 (curvature-guided init)~~ ✅ เสร็จแล้ว (12 มิ.ย. 2569) — 2 ไฟล์ใหม่:
   - `src/curvature_init.py` — โหลด coarse mesh → density map (S1) → sample seeds ตามความหนาแน่น + per-point triangle scale จาก k-NN spacing (CPU ล้วน) ทดสอบกับ buddha แล้ว: 15,000 seeds, scale ต่างกัน ~4.5 เท่าระหว่างโซนโค้ง/แบน (ดู `output/mesh_coarse_curv_init_scatter.png`)
   - `src/diffsoup_train.py` — สำเนา `01_mip360.py` ที่เพิ่ม `--init {random,curvature}` + `--init_npz` + `--max_faces` (ลูป training/loss/resample เหมือนเดิมทุกอย่างเพื่อเทียบแฟร์ ๆ) ระบุที่ตั้ง repo ผ่าน env `DIFFSOUP_ROOT` (default `D:\Project\diffsoup`)
5. **งานถัดไป (S3):** รันเทียบ random vs curvature ที่ `--downscale 4` budget สามเหลี่ยมเท่ากัน → เทียบ PSNR/SSIM

**คำสั่งรัน S2 (สร้าง init):**

```powershell
.venv\Scripts\python.exe src\curvature_init.py output\buddha_sfm\mesh_coarse.ply `
    --n-points 15000 --out output\mesh_coarse_curv_init.npz
```

**คำสั่งรันเทียบ (S3, หลัง baseline เสร็จ):**

```powershell
$env:PYTHONUTF8 = "1"
# ฝั่ง curvature-guided
.venv\Scripts\python.exe src\diffsoup_train.py --scene_root output\buddha_sfm\dense `
    --init curvature --init_npz output\mesh_coarse_curv_init.npz `
    --downscale 4 --batch_size 2 --out_dir output\diffsoup_buddha_curv_d4
# ฝั่ง random (คู่เทียบที่ downscale เดียวกัน)
.venv\Scripts\python.exe src\diffsoup_train.py --scene_root output\buddha_sfm\dense `
    --init random --downscale 4 --batch_size 2 --out_dir output\diffsoup_buddha_rand_d4
```

**คำสั่งรันกับ scene ของเรา:**

```powershell
$env:PYTHONUTF8 = "1"
cd D:\Project\diffsoup
D:\Project\CG-Soup-for-Digital-Dentistry\.venv\Scripts\python.exe examples\01_mip360.py `
    --scene_root D:\Project\CG-Soup-for-Digital-Dentistry\output\buddha_sfm\dense `
    --downscale 1 --batch_size 2 `
    --out_dir D:\Project\CG-Soup-for-Digital-Dentistry\output\diffsoup_buddha_baseline
```

ผล baseline 10,000 steps อยู่ที่ `output/diffsoup_buddha_baseline/` (PSNR/SSIM ใน `test_views/metrics.txt`)
