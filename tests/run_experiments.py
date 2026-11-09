import json, subprocess, sys, time
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'B22_EXPERIMENTAL_RESULTS.md'
PAYLOAD = ROOT / 'tests' / 'payloads'

def post_file(url, field='file', filename='benign.php', content=None, content_type='application/octet-stream'):
    boundary = 'B22Boundary'
    data = content if content is not None else (PAYLOAD / filename).read_bytes()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode() + data + f'\r\n--{boundary}--\r\n'.encode())
    req = request.Request(url, body, {'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
    try:
        with request.urlopen(req, timeout=8) as r: return r.status, r.read().decode(errors='replace')
    except Exception as e:
        return getattr(e, 'code', 0), str(e)

def get(url):
    try:
        with request.urlopen(url, timeout=8) as r: return r.status, r.read().decode(errors='replace')
    except Exception as e: return getattr(e, 'code', 0), str(e)

def php_upload(scenario, filename, content=None, content_type='application/octet-stream'):
    return post_file(f'http://127.0.0.1:18081/vuln_upload.php?scenario={scenario}', filename=filename, content=content, content_type=content_type)

def preflight():
    """Do not replace previous evidence when the local lab is unavailable."""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, timeout=20)
        if result.returncode != 0:
            return False, 'Docker Engine is unavailable. Start Docker Desktop first.'
    except (OSError, subprocess.TimeoutExpired):
        return False, 'Docker is missing or did not respond.'
    for port in (18081, 18082):
        code, _ = get(f'http://127.0.0.1:{port}/')
        if code != 200:
            return False, f'Local lab on port {port} is not ready (HTTP {code}). Run docker compose up -d --build.'
    return True, 'Local lab is ready.'

def main():
    ready, message = preflight()
    if not ready:
        print(f'BLOCKED: {message} Existing reports were not modified.', file=sys.stderr)
        return 2
    subprocess.run([sys.executable, str(ROOT/'tests'/'generate_payloads.py')], check=True)
    rows = []
    code, body = php_upload('content_type', 'benign.php', content_type='image/jpeg')
    rows.append(('PHP vulnerable accepts PHP with spoofed image Content-Type', code == 200 and 'stored' in body, f'HTTP {code}'))
    code, body = get('http://127.0.0.1:18081/uploads/benign.php')
    rows.append(('PHP executes benign marker', code == 200 and body == 'B22_UFU_EXEC_SUCCESS', f'HTTP {code}'))
    for scenario, filename, data, ctype, expected in [
        ('content_type', 'spoof.jpg', b'not an image', 'image/jpeg', 200),
        ('double_ext', 'double.php.jpg', (PAYLOAD / 'benign.php').read_bytes(), 'image/jpeg', 200),
        ('weak_strip', 'test.p.phphp', b'B22 weak-strip scenario', 'text/plain', 200),
        ('null_byte_sim', 'legacy.php%00.jpg', b'B22 null-byte simulation', 'image/jpeg', 200),
        ('magic_bytes', 'magic.gif', (PAYLOAD / 'gif-header.bin').read_bytes(), 'application/octet-stream', 200),
        ('exif_polyglot', 'polyglot.png', (PAYLOAD / 'polyglot.png').read_bytes(), 'image/png', 200),
        ('path_traversal', '../traversal_test.php', (PAYLOAD / 'benign.php').read_bytes(), 'application/x-php', 200),
    ]:
        code, body = php_upload(scenario, filename, data, ctype)
        ok = code == expected and json.loads(body).get('stored') is True
        rows.append((f'PHP vulnerable scenario {scenario} accepts demonstration input', ok, f'HTTP {code}'))
    code, body = get('http://127.0.0.1:18081/uploads/double.php.jpg')
    rows.append(('Apache AddHandler executes double-extension benign PHP marker', code == 200 and body == 'B22_UFU_EXEC_SUCCESS', f'HTTP {code}'))
    code, body = get('http://127.0.0.1:18081/uploads/traversal_test.php')
    rows.append(('Traversal upload escapes sub/ PHP restriction to parent uploads/', code == 200 and body == 'B22_UFU_EXEC_SUCCESS', f'HTTP {code}'))
    code, body = get('http://127.0.0.1:18081/lfi_simulator.php?file=traversal_test.php')
    rows.append(('LFI simulator includes only a file under uploads/', code == 200 and body == 'B22_UFU_EXEC_SUCCESS', f'HTTP {code}'))
    code, _ = get('http://127.0.0.1:18081/lfi_simulator.php?file=../../etc/passwd')
    rows.append(('LFI simulator rejects path outside uploads/', code == 403, f'HTTP {code}'))
    code, body = get('http://127.0.0.1:18081/lfi_simulator.php?file=polyglot.png')
    rows.append(('Image polyglot plus restricted LFI executes appended benign PHP', code == 200 and body.endswith('B22_UFU_EXEC_SUCCESS') and '<?php' not in body, f'HTTP {code}'))
    code, _ = php_upload('path_traversal', 'blocked.php', (PAYLOAD / 'benign.php').read_bytes())
    code, body = get('http://127.0.0.1:18081/uploads/sub/blocked.php')
    rows.append(('Apache disables PHP execution inside uploads/sub/', code == 200 and body == '<?php echo "B22_UFU_EXEC_SUCCESS"; ?>', f'HTTP {code}'))
    code, body = post_file('http://127.0.0.1:18081/defended_upload.php', filename='marker.png', content=(PAYLOAD / 'marker.png').read_bytes(), content_type='image/png')
    try:
        result = json.loads(body)
        file_exists = subprocess.run(['docker', 'compose', '-f', str(ROOT / 'docker-compose.yml'), 'exec', '-T', 'php-lab', 'test', '-f', '/var/www/storage_outside_webroot/' + result['id']], capture_output=True).returncode == 0
        ok = code == 201 and result['stored'] and result['marker_present'] is False and file_exists
    except (ValueError, KeyError):
        ok = False
    rows.append(('PHP defense re-encodes image, removes appended marker and stores outside webroot', ok, f'HTTP {code}'))
    code, _ = post_file('http://127.0.0.1:18081/defended_upload.php', filename='fake.png', content=(PAYLOAD / 'benign.php').read_bytes(), content_type='image/png')
    rows.append(('PHP defense rejects PHP renamed as PNG', code == 415, f'HTTP {code}'))
    code, _ = post_file('http://127.0.0.1:18081/defended_upload.php', filename='benign.php', content_type='application/x-php')
    rows.append(('PHP defended rejects PHP', code == 415, f'HTTP {code}'))
    code, body = post_file('http://127.0.0.1:18082/vuln/public-upload', filename='node-marker.html', content=(PAYLOAD / 'benign.html').read_bytes(), content_type='text/html')
    node_public = json.loads(body).get('url') if code == 201 else None
    public_code, public_body = get('http://127.0.0.1:18082' + node_public) if node_public else (0, '')
    rows.append(('Node routed vulnerable endpoint stores and serves benign HTML marker', code == 201 and public_code == 200 and public_body == '<!-- B22_XSS_MARKER -->', f'POST {code}, GET {public_code}'))
    code, body = post_file('http://127.0.0.1:18082/defended/upload', filename='marker.png', content=(PAYLOAD / 'marker.png').read_bytes(), content_type='image/png')
    try:
        result = json.loads(body)
        defended_id = result['id']
        stored = subprocess.run(['docker', 'compose', '-f', str(ROOT / 'docker-compose.yml'), 'exec', '-T', 'node-lab', 'test', '-f', '/app/storage_outside_webroot/' + defended_id], capture_output=True).returncode == 0
        rows.append(('Node sharp re-encodes PNG and strips appended benign marker outside webroot', code == 201 and result['stored'] and result['marker_present'] is False and stored, f'HTTP {code}'))
        get_req = request.Request('http://127.0.0.1:18082/defended/file/' + defended_id, method='GET')
        with request.urlopen(get_req, timeout=8) as response:
            headers = response.headers
            body_bytes = response.read()
            secure_headers = headers.get('X-Content-Type-Options') == 'nosniff' and headers.get('Content-Disposition', '').startswith('attachment') and headers.get('Content-Security-Policy') == "default-src 'none'"
            rows.append(('Node defended retrieval sets download and security headers', secure_headers and body_bytes.startswith(bytes.fromhex('ffd8ff')), f'HTTP {response.status}'))
    except (ValueError, KeyError, OSError):
        rows.append(('Node sharp re-encodes PNG and strips appended benign marker outside webroot', False, f'HTTP {code}'))
        rows.append(('Node defended retrieval sets download and security headers', False, 'No defended file ID'))
    code, _ = post_file('http://127.0.0.1:18082/defended/upload', filename='fake.jpg', content=(PAYLOAD / 'benign.php').read_bytes(), content_type='image/jpeg')
    rows.append(('Node defense rejects spoofed image MIME and extension', code == 415, f'HTTP {code}'))
    code, body = post_file('http://127.0.0.1:18082/vuln/traversal-upload', filename='../traversal_node.html', content=(PAYLOAD / 'benign.html').read_bytes(), content_type='image/jpeg')
    try:
        traversal = json.loads(body)
        escaped = traversal.get('original') == '../traversal_node.html'
        check_code, check_body = get('http://127.0.0.1:18082/traversal_node.html')
        escaped = escaped and check_code == 200 and check_body == '<!-- B22_XSS_MARKER -->'
    except ValueError:
        escaped = False
    rows.append(('Node traversal endpoint reports whether original filename escapes upload directory', code == 201 and escaped, f'HTTP {code}'))
    code, _ = post_file('http://127.0.0.1:18082/defended/upload', filename='large.jpg', content=b'A' * (2 * 1024 * 1024 + 1), content_type='image/jpeg')
    rows.append(('Node defended rejects oversized file', code == 413, f'HTTP {code}'))
    for label, url in [
        ('PHP', 'http://127.0.0.1:18081/defended_upload.php'),
        ('Node', 'http://127.0.0.1:18082/defended/upload'),
    ]:
        for case, filename, data, expected in [
            ('empty image', 'empty.png', b'', 415),
            ('truncated PNG', 'broken.png', bytes.fromhex('89504e470d0a1a0a'), 415),
            ('extension mismatch', 'wrong.jpg', (PAYLOAD / 'marker.png').read_bytes(), 415),
        ]:
            code, _ = post_file(url, filename=filename, content=data, content_type='image/png')
            rows.append((f'{label} defense rejects {case}', code == expected, f'HTTP {code}'))
        code, _ = post_file(url, field='unexpected', filename='marker.png', content_type='image/png')
        rows.append((f'{label} defense rejects unexpected file field', code == 400, f'HTTP {code}'))
    for size in (1048577, 2097153, 3145729):
        code, _ = post_file('http://127.0.0.1:18081/defended_upload.php', filename='large.png', content=b'A' * size, content_type='image/png')
        rows.append((f'PHP defense rejects oversized upload ({size} bytes)', code == 413, f'HTTP {code}'))
    try:
        semgrep = subprocess.run(['docker','run','--rm','-v',f'{ROOT}:/src:ro','semgrep/semgrep','semgrep','scan','--metrics=off','--json','--config','/src/semgrep/b22-ufu-rules.yaml','/src/php-lab/src','/src/node-lab/server.js'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    except (subprocess.TimeoutExpired, OSError) as exc:
        semgrep = subprocess.CompletedProcess([], 124, '', str(exc))
    try:
        scan = json.loads(semgrep.stdout)
        ids = {item['check_id'].split('.')[-1] for item in scan.get('results', [])}
        sast_ok = semgrep.returncode == 0 and not scan.get('errors') and {'b22-php-unrestricted-move-upload', 'b22-node-multer-webroot'} <= ids
    except (ValueError, KeyError):
        sast_ok = False
    rows.append(('SAST detects both intentional vulnerable patterns', sast_ok, f'Exit {semgrep.returncode}'))
    report = ['# B22 Experimental Results', '', '## Scope and safety', 'Local-only Docker lab for unrestricted file upload detection. Payloads contain only `B22_UFU_EXEC_SUCCESS` or `B22_XSS_MARKER`; no command execution payloads were used.', '', '## Verification results', '| Test | Result | Detail |', '|---|---|---|']
    report += [f'| {n} | {"BLOCKED" if d == "HTTP 0" else "PASS" if ok else "FAIL"} | {d} |' for n, ok, d in rows]
    report += ['', '## SAST (Semgrep)', f'- Exit code: `{semgrep.returncode}`', '```text', semgrep.stdout[-12000:] or semgrep.stderr[-12000:], '```', '', '## Interpretation (C2 / C4)', '- C2: PHP marker execution demonstrates server-side interpretation of an uploaded file. Node vulnerable routes serve arbitrary uploaded files; HTML marker retrieval is not executed XSS.', '- Node traversal is reported only if Multer preserves the submitted parent path and writes outside public/uploads.', '- C4: PHP and Node defended routes validate signatures/content and re-encode images before storing outside the webroot.', '- Semgrep rules are narrow structural heuristics for this lab, not proof of absence of upload vulnerabilities.', '- lfi_simulator.php uses include with a canonical-path boundary restricted to uploads/.', '- HTTP 0 means infrastructure BLOCKED, never a successful security test.', '- This lab is educational and is bound to loopback by Docker Compose.']
    OUT.write_text('\n'.join(report) + '\n', encoding='utf-8')
    print('\n'.join(report))
    (ROOT / 'docs' / 'semgrep.log').write_text(semgrep.stdout + semgrep.stderr, encoding='utf-8')
    (ROOT / 'docs' / 'verification.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return 0 if all(ok for _, ok, _ in rows) and semgrep.returncode == 0 else 1
if __name__ == '__main__': raise SystemExit(main())
