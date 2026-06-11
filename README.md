# CG-Soup (ใบหน้าทั้งหน้า) + Jaw Tracking

แผนงาน: ดู `plan.md`

## โครงสร้าง
- `src/curvature_density.py` — โมดูล S1: principal curvatures + QEM → density map
- `data/` — mesh ทดสอบสาธารณะ (max-planck, igea จาก common-3d-test-models)
- `output/` — density map (PLY มีสี เปิดใน MeshLab ได้ + PNG หลายมุมมอง)
- `docs/` — ร่างเอกสารแจ้งขอบเขต + ประเด็น API contract กับ Team 1

## รัน
ใช้ conda env `dent` (มี numpy/scipy/trimesh/open3d/matplotlib):

```bash
~/miniconda3/envs/dent/bin/python src/curvature_density.py data/max-planck.obj
```

ผลลัพธ์อยู่ใน `output/<ชื่อ mesh>_density.{ply,png}` — สีแดง = ความหนาแน่นสามเหลี่ยมสูง
