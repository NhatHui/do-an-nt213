from pathlib import Path
import struct, zlib
OUT = Path(__file__).parent / 'payloads'
OUT.mkdir(exist_ok=True)
(OUT / 'benign.php').write_text('<?php echo "B22_UFU_EXEC_SUCCESS"; ?>', encoding='utf-8')
(OUT / 'benign.html').write_text('<!-- B22_XSS_MARKER -->', encoding='utf-8')
(OUT / 'benign.txt').write_text('B22 benign upload verification', encoding='utf-8')
# A 1x1 RGB PNG with a benign marker appended after IEND; GD must remove it.
print(f'Generated payloads in {OUT}')
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
png = bytes.fromhex('89504e470d0a1a0a') + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes([0, 255, 0, 0]))) + chunk(b'IEND', b'')
(OUT / 'marker.png').write_bytes(png + b'B22_UFU_EXEC_SUCCESS')
(OUT / 'polyglot.png').write_bytes(png + b'<?php echo "B22_UFU_EXEC_SUCCESS"; ?>')
(OUT / 'gif-header.bin').write_bytes(b'GIF89aB22 benign marker')
(OUT / 'null-byte-name.jpg').write_bytes(b'B22 benign null-byte simulation')
