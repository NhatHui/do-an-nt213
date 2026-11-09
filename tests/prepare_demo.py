"""Generate deterministic, harmless local demo files using only the standard library."""
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parents[1] / 'DEMO_MAU'

def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

def main():
    OUT.mkdir(exist_ok=True)
    width, height = 240, 160
    raw = b''.join(b'\0' + bytes((30, 110, 85)) * width for _ in range(height))
    png = bytes.fromhex('89504e470d0a1a0a')
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    marker = b'<?php echo "B22_UFU_EXEC_SUCCESS"; ?>'
    # A valid PNG with an ancillary text chunk: the size test is not a fake-image test.
    large = png[:-12] + chunk(b'tEXt', b'Comment\0' + b'A' * (2 * 1024 * 1024)) + png[-12:]
    files = {
        '01_anh_hop_le.png': png,
        '02_gia_anh.png': b'B22 demo: this is plain text, not an image.',
        '03_marker_vo_hai.php': marker,
        '04_hai_duoi.php.jpg': marker,
        '05_anh_kem_marker.png': png + marker,
        '06_anh_vuot_2MiB.png': large,
        '07_du_lieu.csv': b'id,name\n1,B22 demo\n',
        '08_html_marker.html': b'<!-- B22_XSS_MARKER -->',
    }
    for name, data in files.items():
        (OUT / name).write_bytes(data)
        print(f'{name}: {len(data)} bytes')

if __name__ == '__main__':
    main()