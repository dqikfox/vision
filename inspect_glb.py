"""
Quick GLB file inspector - checks if the file is valid
"""
import struct
from pathlib import Path

glb_path = Path("C:/project/vision/assets/ultron-avatar.glb")

print(f"Inspecting: {glb_path}")
print(f"Exists: {glb_path.exists()}")
print(f"Size: {glb_path.stat().st_size:,} bytes")

with open(glb_path, 'rb') as f:
    # Read GLB header
    magic = f.read(4)
    version = struct.unpack('<I', f.read(4))[0]
    length = struct.unpack('<I', f.read(4))[0]

    print("\nGLB Header:")
    print(f"  Magic: {magic} (should be b'glTF')")
    print(f"  Version: {version}")
    print(f"  Total Length: {length:,} bytes")

    # Read first chunk
    chunk_length = struct.unpack('<I', f.read(4))[0]
    chunk_type = f.read(4)

    print("\nFirst Chunk:")
    print(f"  Length: {chunk_length:,} bytes")
    print(f"  Type: {chunk_type} (should be b'JSON')")

    if magic == b'glTF' and chunk_type == b'JSON':
        print("\n✅ Valid GLB file!")

        # Read JSON chunk to see structure
        json_data = f.read(min(chunk_length, 500))
        print("\nFirst 500 chars of JSON:")
        print(json_data.decode('utf-8', errors='ignore'))
    else:
        print("\n❌ Invalid GLB file!")
