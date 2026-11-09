'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const php = document.body.dataset.platform === 'php';
  const scenarios = php ? [
    ['content_type', 'Tin Content-Type từ client', 'Chấp nhận MIME image/jpeg hoặc image/png và tệp dưới 100.000 byte, không xác minh nội dung.'],
    ['double_ext', 'Double extension', 'Chỉ kiểm tra đuôi jpg/png. Tác động thực thi còn phụ thuộc cấu hình Apache của lab.'],
    ['weak_strip', 'Lọc tên bằng xóa chuỗi', 'Xóa chuỗi php khỏi tên, không xác minh định dạng.'],
    ['null_byte_sim', 'Null byte — mô phỏng', 'Mô phỏng cắt tên tại %00; không phải bypass null byte trên PHP hiện đại.'],
    ['magic_bytes', 'Chỉ kiểm tra magic bytes', 'Chỉ kiểm tra 6 byte GIF87a hoặc GIF89a ở đầu tệp.'],
    ['exif_polyglot', 'Ảnh có dữ liệu bổ sung', 'Kiểm tra đuôi và thông tin ảnh nhưng không tái mã hóa; mẫu có PHP nối sau ảnh.'],
    ['path_traversal', 'Path traversal', 'Ghép tên vào uploads/sub; đường dẫn có thể ảnh hưởng vị trí lưu. Chỉ thử trong lab.']
  ] : [
    ['public', 'Public upload — lưu vào vùng static', 'Lưu tệp bất kỳ vào vùng public. Trả HTML marker không chứng minh XSS đã thực thi.'],
    ['traversal', 'Path traversal — giữ đường dẫn gốc', 'Cố ý bật preservePath, dùng tên gốc và chỉ tin MIME image/jpeg. Đây không phải mặc định của Multer.']
  ];
  let selected = null, busy = false, latest = null;
  const history = [];
  scenarios.forEach(([value, label]) => $('scenario').add(new Option(label, value)));
  const defended = () => document.querySelector('input[name="mode"]:checked').value === 'defended';
  function endpoint() {
    return defended() ? (php ? '/defended_upload.php' : '/defended/upload') :
      (php ? '/vuln_upload.php?scenario=' + $('scenario').value : '/vuln/' + ($('scenario').value === 'public' ? 'public-upload' : 'traversal-upload'));
  }
  function policy() {
    $('scenario-field').hidden = defended();
    $('policy').textContent = defended() ?
      `Chỉ JPEG/PNG; tối đa ${php ? '1' : '2'} MiB và 4 triệu pixel. ${php ? 'GD tái mã hóa cùng loại ảnh.' : 'Sharp chuyển ảnh sang JPEG.'} Lưu ngoài vùng public.` : scenarios.find(s => s[0] === $('scenario').value)[2];
    $('endpoint').textContent = endpoint();
  }
  function size(n) { return n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KiB` : `${(n / 1048576).toFixed(2)} MiB`; }
  function choose(file) {
    selected = file || null;
    $('filename').value = file ? file.name : '';
    $('mime').value = file ? file.type || 'application/octet-stream' : '';
    $('file-info').textContent = file ? `${file.name} · ${size(file.size)} · ${file.type || 'không khai báo MIME'}` : 'Chưa chọn tệp.';
    $('form-message').textContent = '';
  }
  document.querySelectorAll('input[name="mode"]').forEach(el => el.addEventListener('change', policy));
  $('scenario').addEventListener('change', policy);
  $('file').addEventListener('change', () => choose($('file').files[0]));
  ['dragenter', 'dragover'].forEach(name => $('dropzone').addEventListener(name, event => {
    event.preventDefault(); if (!busy) $('dropzone').classList.add('dragging');
  }));
  ['dragleave', 'drop'].forEach(name => $('dropzone').addEventListener(name, event => {
    event.preventDefault(); $('dropzone').classList.remove('dragging');
    if (name === 'drop' && !busy) {
      if (event.dataTransfer.files.length !== 1) { $('form-message').textContent = 'Vui lòng thả đúng một tệp.'; return; }
      $('file').value = ''; choose(event.dataTransfer.files[0]);
    }
  }));
  const marker = '<?php echo "B22_UFU_EXEC_SUCCESS"; ?>';
  function png() {
    const canvas = document.createElement('canvas'); canvas.width = 96; canvas.height = 64;
    const ctx = canvas.getContext('2d'); ctx.fillStyle = '#176b59'; ctx.fillRect(0, 0, 96, 64);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 24px sans-serif'; ctx.fillText('B22', 23, 40);
    return Uint8Array.from(atob(canvas.toDataURL('image/png').split(',')[1]), c => c.charCodeAt(0));
  }
  document.querySelectorAll('[data-sample]').forEach(button => button.addEventListener('click', () => {
    if (busy) return;
    const sample = button.dataset.sample;
    const files = {
      image: () => new File([png()], 'demo-image.png', {type: 'image/png'}),
      fake: () => new File(['B22: this is text, not a PNG image.'], 'fake-image.png', {type: 'image/png'}),
      marker: () => new File([marker], 'demo-marker.php', {type: 'image/jpeg'}),
      polyglot: () => new File([png(), marker], 'demo-polyglot.png', {type: 'image/png'}),
      html: () => new File(['<!-- B22_XSS_MARKER -->'], 'demo-marker.html', {type: 'text/html'})
    };
    $('file').value = ''; choose(files[sample]());
    $('sample-help').textContent = sample === 'marker' ? 'PHP chỉ in marker; MIME khai báo image/jpeg được chọn cố ý để đối chiếu kiểm tra yếu.' :
      sample === 'polyglot' ? 'PNG hợp lệ có PHP marker nối thêm. Tái mã hóa được kỳ vọng loại bỏ dữ liệu nối.' :
      sample === 'html' ? 'Chỉ là chú thích HTML, không có JavaScript và không chứng minh XSS.' : 'Mẫu đã sẵn sàng. Nhấn Gửi tệp & kiểm tra để thực hiện request thật.';
  }));
  function fact(label, value) {
    const dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = label; dd.textContent = String(value); $('facts').append(dt, dd);
  }
  function link(label, path) {
    const a = document.createElement('a'); a.textContent = label; a.href = path; a.target = '_blank'; a.rel = 'noopener noreferrer'; $('file-actions').append(a);
  }
  function renderHistory() {
    $('history').replaceChildren();
    if (!history.length) { const tr = document.createElement('tr'), td = document.createElement('td'); td.colSpan = 5; td.textContent = 'Chưa có yêu cầu nào.'; tr.append(td); $('history').append(tr); }
    history.forEach(row => {
      const tr = document.createElement('tr');
      [row.time, row.mode, row.filename, row.status || 'Lỗi mạng', row.ms + ' ms'].forEach(value => { const td = document.createElement('td'); td.textContent = value; tr.append(td); });
      $('history').append(tr);
    });
  }
  function render(record, data, ok) {
    $('empty').hidden = true; $('result').hidden = false;
    $('http-code').textContent = record.status || '—'; $('duration').textContent = record.ms + ' ms'; $('sent-size').textContent = size(record.bytes);
    $('status').textContent = record.status ? `HTTP ${record.status}` : 'Lỗi kết nối';
    $('status').className = 'status ' + (ok ? 'good' : 'bad');
    $('interpretation').textContent = !record.status ? 'Không nhận được phản hồi. Kiểm tra container và kết nối, sau đó thử lại.' :
      record.status >= 500 ? 'Máy chủ gặp lỗi xử lý. Đây không phải bằng chứng phòng vệ thành công.' :
      !ok ? 'Máy chủ từ chối yêu cầu. Đọc thông báo bên dưới để xác định điều kiện không đạt.' :
      data && data.stored === true ? (record.defended ? 'Máy chủ báo đã xử lý và lưu tệp. Kiểm tra ID và marker; đây không phải chứng nhận tệp hoàn toàn an toàn.' : 'Nhánh có lỗ hổng báo đã lưu tệp. Việc lưu được không tự chứng minh đã thực thi mã.') :
      'Máy chủ trả HTTP thành công nhưng chưa xác nhận stored=true. Không kết luận upload thành công chỉ từ mã HTTP.';
    $('response').textContent = data ? JSON.stringify(data, null, 2) : record.body || '(Phản hồi rỗng)';
    $('headers').textContent = Object.entries(record.headers).map(([k,v]) => `${k}: ${v}`).join('\n') || '(Không có phản hồi HTTP)';
    $('facts').replaceChildren(); $('file-actions').replaceChildren();
    fact('Endpoint', record.endpoint); fact('Tên đã gửi', record.filename); fact('MIME khai báo', record.mime);
    if (data && typeof data === 'object') {
      if (typeof data.id === 'string') fact('ID tệp', data.id);
      if (typeof data.path === 'string') fact('Đường dẫn', data.path);
      if (typeof data.marker_present === 'boolean') fact('Còn marker?', data.marker_present ? 'Có' : 'Không thấy chuỗi marker');
      if (ok && data.stored === true) {
        // Never interpolate untrusted response fields into HTML or executable URLs.
        if (record.defended && !php && typeof data.id === 'string' && /^[0-9a-f-]{36}\.jpg$/.test(data.id)) link('Tải JPEG đã xử lý', '/defended/file/' + encodeURIComponent(data.id));
        if (!record.defended && typeof data.url === 'string') {
          const url = new URL(data.url, location.origin);
          if (url.origin === location.origin && url.pathname.startsWith('/uploads/')) {
            link('Mở tệp đã lưu ↗', url.href);
            if (php) link('LFI simulator (chỉ trong lab) ↗', '/lfi_simulator.php?file=' + encodeURIComponent(decodeURIComponent(url.pathname.slice('/uploads/'.length))));
          }
        }
        if (record.defended && php) fact('Truy xuất', 'PHP chưa cung cấp endpoint tải tệp ngoài webroot.');
      }
    }
  }
  function setBusy(value) {
    busy = value;
    $('upload-form').querySelectorAll('input, select, button').forEach(el => el.disabled = value);
    $('submit').textContent = value ? 'Đang gửi và chờ phản hồi…' : 'Gửi tệp & kiểm tra →';
    $('upload-form').setAttribute('aria-busy', String(value));
  }
  $('upload-form').addEventListener('submit', async event => {
    event.preventDefault(); if (busy) return;
    if (!selected) { $('form-message').textContent = 'Chọn một tệp hoặc mẫu demo trước khi gửi.'; $('file').focus(); return; }
    const filename = $('filename').value.trim() || selected.name;
    const mime = $('mime').value.trim() || selected.type || 'application/octet-stream';
    if (/[\r\n\x00]/.test(filename) || !/^[\w!#$&^.+-]+\/[\w!#$&^.+-]+$/.test(mime)) {
      $('form-message').textContent = 'Tên không được chứa ký tự điều khiển; MIME cần có dạng image/png.'; return;
    }
    const record = {time: new Date().toLocaleTimeString('vi-VN'), platform: php ? 'PHP' : 'Node.js', mode: defended() ? 'Phòng vệ' : 'Có lỗ hổng', defended: defended(), endpoint: endpoint(), filename, mime, bytes: selected.size, headers: {}, body: '', status: 0};
    const form = new FormData(); form.append('file', new Blob([selected], {type: mime}), filename);
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 30000);
    const start = performance.now(); let data = null, ok = false;
    setBusy(true); $('form-message').textContent = ''; $('status').textContent = 'Đang gửi…'; $('status').className = 'status';
    try {
      const response = await fetch(record.endpoint, {method: 'POST', body: form, signal: controller.signal});
      record.status = response.status; ok = response.ok;
      record.headers = Object.fromEntries(response.headers.entries()); record.body = await response.text();
      try { data = JSON.parse(record.body); } catch (_) { /* Preserve non-JSON responses as plain text. */ }
    } catch (error) {
      record.body = error.name === 'AbortError' ? 'Hết thời gian chờ 30 giây. Máy chủ có thể vẫn đang xử lý yêu cầu.' : 'Không thể kết nối tới máy chủ: ' + error.message;
    } finally {
      clearTimeout(timer); record.ms = Math.round(performance.now() - start); latest = record;
      setBusy(false); render(record, data, ok);
      history.unshift(record); if (history.length > 10) history.pop(); renderHistory();
    }
  });
  $('reset').addEventListener('click', () => {
    if (busy) return;
    HTMLFormElement.prototype.reset.call($('upload-form')); choose(null); policy();
    $('sample-help').textContent = 'Mẫu được tạo ngay trong trình duyệt, không chạy lệnh hệ điều hành.';
    $('result').hidden = true; $('empty').hidden = false; $('status').textContent = 'Chưa gửi'; $('status').className = 'status'; latest = null;
  });
  $('clear-history').addEventListener('click', () => { history.length = 0; renderHistory(); });
  $('save-result').addEventListener('click', () => {
    if (!latest) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(latest, null, 2)], {type:'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = 'b22-upload-result.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  policy();
})();