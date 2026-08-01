"""Quick diagnostic: prints the real file type based on file header bytes."""
from pathlib import Path

file_path = input("Enter file path to check: ").strip().strip('"').strip("'")

with open(file_path, "rb") as f:
    header = f.read(16)

print(f"\nFile: {Path(file_path).name}")
print(f"First 16 bytes (hex): {header.hex()}")
print(f"First 16 bytes (raw): {header}")

if header.startswith(b"%PDF"):
    print("-> This IS a real PDF")
elif header.startswith(b"\xff\xd8\xff"):
    print("-> This IS a real JPEG image")
elif header.startswith(b"\x89PNG"):
    print("-> This IS a real PNG image")
elif header.startswith(b"RIFF") and b"WEBP" in header:
    print("-> This is a WEBP image (common for WhatsApp) - needs conversion")
else:
    print("-> Unknown format - not a standard PDF/JPEG/PNG")
    