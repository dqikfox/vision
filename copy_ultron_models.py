"""
Copy all Ultron GLB models to assets for testing
"""
import shutil
from pathlib import Path

source_dir = Path("F:/ultron_agent/Avatar")
dest_dir = Path("C:/project/vision/assets")
dest_dir.mkdir(exist_ok=True)

models = [
    ("ultron+xps.glb", "ultron-v1.glb"),
    ("ultron+xps3.glb", "ultron-v3.glb"),
    ("ultron+xps4.glb", "ultron-v4.glb"),
    ("ultron+xps5.glb", "ultron-v5.glb"),
    ("ultron_exported.glb", "ultron-exported.glb"),
]

print("Copying Ultron model variants...")
for src_name, dest_name in models:
    src = source_dir / src_name
    if src.exists():
        dest = dest_dir / dest_name
        shutil.copy2(src, dest)
        print(f"✓ {src_name} → {dest_name} ({src.stat().st_size:,} bytes)")
    else:
        print(f"✗ {src_name} not found")

print(f"\nDone! Models copied to {dest_dir}")
